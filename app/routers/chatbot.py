from fastapi import APIRouter, Depends, HTTPException
from app.models import Reservation, DeleteReservation, ReservationBot
from app.db import DB
from app.dependencies import check_api_key
from uuid import uuid4
from app.functions import get_requirements_query

router = APIRouter(
    prefix="/chatbot",
    tags=["chatbot"],
    dependencies=[Depends(check_api_key)]
)

@router.get("/zones")
async def get_Zones():
    try:
        async with DB() as db:
            query = '''
                SELECT [ZoneName], [Description] 
                FROM [dbo].[Zone];
            '''
            results = await db.execute_query(query)

            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'Zone': f"{row[0]}: {row[1]}"
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
            group_code = str(uuid4())[:7]
            query ='''
                DECLARE @GroupID INT;
                INSERT INTO [dbo].[ReservationGroup] (GroupCode)
                OUTPUT INSERTED.GroupID
                VALUES (?);

                SET @GroupID = SCOPE_IDENTITY(); 

                INSERT INTO [dbo].[Reservation] (GroupId, UserId, SpaceId, ScheduleId, UserRequirements) 
                VALUES (@GroupID, ?, ?, ?, '');

                UPDATE [dbo].[Schedule] SET Occupied = 1 WHERE ScheduleId = ?;

                MERGE INTO [dbo].[Statistic] AS target
                USING (SELECT ? AS UserId) AS source (UserId)
                ON target.UserId = source.UserId
                WHEN MATCHED THEN
                    UPDATE SET Reservations = target.Reservations + 1,
                            StudyHours = target.StudyHours + 1
                WHEN NOT MATCHED THEN
                    INSERT (UserId, Reservations, StudyHours)
                    VALUES (source.UserId, 1, 1);

              '''
            if len(res.user_requirements) > 0:
                query += get_requirements_query(res.user_requirements)
            print(query)
            params = (group_code, res.user_id, res.space_id, res.schedule_id, res.schedule_id, res.user_id)
            results = await db.execute_query_insert(query=query, params=params)
            return {"message": "Reservation created successfully", "results": results}
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
            query = "SELECT [ScheduleId] from dbo.Schedule WHERE [Day] = ? AND [StartHour] = ?"
            params = (dates[0], dates[1])
            results = await db.execute_query(query, params)
            if len(results) == 0:
                raise HTTPException(status_code=404, detail="Schedule not found")
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