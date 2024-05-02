from fastapi import APIRouter, Depends, HTTPException
from app.models import Reservation, DeleteReservation, ReservationBot
from app.db import DB
from app.dependencies import check_api_key
from uuid import uuid4
from app.functions import get_requirements_query
from datetime import datetime, timedelta

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
    
@router.get("/space/{SpaceName}")
async def get_space_description(SpaceName: str):
    try:
        async with DB() as db:
            query = '''
                SELECT [SpaceId], [Description]
                FROM [dbo].[Space]
                WHERE LOWER(Name) = LOWER(?);
            '''
            params = (SpaceName,)
            results = await db.execute_query(query, params)

            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'SpaceId': row[0],
                    'Description': row[1]
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schedules/{SpaceId}/{Day}")
async def get_schedule(SpaceId: int,Day: str):
    today = datetime.now()
    actual_day = today.weekday()  # 0 para lunes, 1 para martes, ..., 6 para domingo
    target_day = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'].index(Day.lower())

    if actual_day <= target_day:
        days_count = target_day - actual_day
    else:
        days_count = 7 - (actual_day - target_day)

    date = today + timedelta(days=days_count)
    final_day =  date.strftime('%Y-%m-%d')
    try:
        async with DB() as db:
            query = '''
                SELECT [StartHour], [EndHour]
                FROM [dbo].[Schedule] 
                WHERE [SpaceId] = ? AND [Day] = ? AND [Occupied] = 0;
                '''
            params = (SpaceId ,final_day,)
            results = await db.execute_query(query, params)
            formatted_results = []
            print(results)
            for row in results:
                formatted_results.append({
                    'StartHour': row[0],
                    'EndHour': row[1]
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/requirements/{SpaceId}")
async def get_space_requirements(SpaceId: int):
    try:
        async with DB() as db:
            query = "EXEC GetSpaceRequirements @SpaceId = ?"
            params = (SpaceId,)
            results = await db.execute_query(query, params)
            formatted_results = []
            print(results)
            for row in results:
                formatted_results.append({
                    'SpaceId': row[0],
                    'RequirementId': row[1],
                    'RequirementName': row[2],
                    'MaxQuantity': row[3]
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schedulesprovider")
async def get_schedules_pro():
    try:
        async with DB() as db:
            query = "SELECT * FROM [dbo].[Schedule]"
            results = await db.execute_query(query)
            formatted_results = []
            print(results)
            for row in results:
                formatted_results.append({
                    'ScheduleId': row[0],
                    'SpaceId': row[1],
                    'Day': row[2],
                    'StartHour': row[3].strftime('%H:%M'),
                    'EndHour': row[4].strftime('%H:%M'),
                    'Occupied': row[5]
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

    today = datetime.now()
    actual_day = today.weekday()  # 0 para lunes, 1 para martes, ..., 6 para domingo
    target_day = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'].index(dates[0].lower())

    if actual_day <= target_day:
        days_count = target_day - actual_day
    else:
        days_count = 7 - (actual_day - target_day)

    date = today + timedelta(days=days_count)
    dates[0] =  date.strftime('%Y-%m-%d')
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