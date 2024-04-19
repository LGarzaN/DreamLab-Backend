from fastapi import APIRouter, Depends, HTTPException
from app.models import Reservation, DeleteReservation
from app.db import DB
from app.dependencies import check_api_key
from uuid import uuid4
from app.functions import get_requirements_query

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
    Crear ReservationGroup
    - Agregar reservacion a tabla de Reservation
    - Marcar Schedule como ocupado
    Agregar requerimientos a UserRequirements
    - Actualizar tabla de Statistics

    formato de userRequirements: "1=1,2=3,4=6"
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
            query += get_requirements_query(res.user_requirements)
            print(query)
            params = (group_code, res.user_id, res.space_id, res.schedule_id, res.schedule_id, res.user_id)
            results = await db.execute_query_insert(query=query, params=params)
            return {"message": "Reservation created successfully", "results": results}
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