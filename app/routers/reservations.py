from fastapi import APIRouter, Depends, HTTPException
from app.models import Reservation, DeleteReservation, ReservationBot
from app.db import DB
from app.dependencies import check_api_key
from app.functions import create_confirmed_reservation

router = APIRouter(
    prefix="/reservations",
    tags=["reservations"],
    dependencies=[Depends(check_api_key)]
)

@router.get("/schedule/{area_id}")
async def get_Schedule(area_id: int):
    try:
        async with DB() as db:
            query = "EXEC GetSchedule @p_SpaceId = ?"
            params = (area_id,)
            results = await db.execute_query(query, params)

            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'ScheduleId': row[0],
                    'Day': row[1].strftime('%Y-%m-%d'),
                    'StartHour': row[2].strftime('%H:%M'),
                    'EndHour': row[3].strftime('%H:%M'),
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/create")
async def create_reservation(res: Reservation):
    """
    Crear una reserva en la base de datos

    formato de userRequirements: "1=1,2=3,4=6"
    donde 1 es el id del requerimiento y 1 es la cantidad
    """
    try:
        async with DB() as db:
            query = "INSERT INTO [dbo].[PendingReservation] (UserId, SpaceId, ScheduleId, UserRequirements) VALUES (?, ?, ?, ?);"
            params = (res.user_id, res.space_id, res.schedule_id, res.user_requirements)
            results = await db.execute_query_insert(query, params)
            return {"message": "Reservation created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
   
    
@router.post("/create/bot")
async def create_reservation_bot(res: ReservationBot):
    """
    Crear una reserva a traves de chatbot

    formato de schedule: "AAAA-MM-DD HH:MM:SS"
    Ejemplo: "2021-06-01 08:00:00"
    """
    dates = res.schedule.split(" ")
    try:
        async with DB() as db:
            query = "SELECT [ScheduleId] from dbo.Schedule WHERE [Day] = ? AND [StartHour] = ? AND [SpaceId] = ? AND [Occupied] = 0;"
            params = (dates[0], dates[1], res.space_id)
            results = await db.execute_query(query, params)
            if len(results) == 0:
                raise HTTPException(status_code=404, detail="Schedule not found or already occupied")
            schedule_id = results[0][0]
            return await create_reservation(Reservation(user_id=res.user_id, space_id=res.space_id, schedule_id=int(schedule_id), user_requirements=res.user_requirements))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get reservations for a specific user
@router.get("/{user_id}")
async def get_reservations(user_id: int):
    try:
        async with DB() as db:
            query = "EXEC GetReservationDetails @UserId = ?"
            params = (user_id,)
            results = await db.execute_query(query, params)
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'Day': row[0].strftime('%Y-%m-%d'),
                    'StartHour': row[1].strftime('%H:%M'),
                    'EndHour': row[2].strftime('%H:%M'),
                    'SpaceName': row[3],
                    'SpaceId': row[4],
                    'RequirementsId': row[5],
                    'RequirementsQuantity': row[6],
                    'GroupCode': row[7]
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/pending/{user_id}")
async def get_pending_reservations(user_id: int):
    try:
        async with DB() as db:
            query = "EXEC GetPendingReservations @UserId = ?"
            params = (user_id,)
            results = await db.execute_query(query, params)
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'PendingReservationId': row[0],
                    'SpaceId': row[1],
                    'Day': row[2].strftime('%Y-%m-%d'),
                    'StartHour': row[3].strftime('%H:%M'),
                    'EndHour': row[4].strftime('%H:%M'),
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/")
async def delete_reservation(body: DeleteReservation):
    try:
        print(body)
        async with DB() as db:
            query = "EXEC CancelReservation @groupCode = ?, @userId = ?;"
            params = (body.group_code, body.user_id)
            results = await db.execute_query_insert(query, params)
            return {"message": "Reservation deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))