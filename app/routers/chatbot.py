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

@router.get("/userid/{UserName}")
async def get_userid(UserName: str):
    """
    Get the UserId for a given UserName.

    Parameters:
        - UserName (str): The username of the user.

    Returns:
        - List[Dict[str, Any]]: A list of dictionaries containing the UserId.

    Raises:
        - HTTPException: If there is an error while executing the query.
    """
    try:
        async with DB() as db:
            query = '''
                SELECT [UserId]
                FROM [dbo].[User]
                WHERE Username = ?;
            '''
            params = (UserName,)
            results = await db.execute_query(query, params)

            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'UserId': row[0],
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/zones")
async def get_Zones():
    """
    Get all the zones.

    Returns:
        - List[Dict[str, str]]: A list of dictionaries containing the ZoneName and Description.

    Raises:
        - HTTPException: If there is an error while executing the query.
    """
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

@router.get("/spaces/zone/{zone_name}")
async def get_spaces_by_zone(zone_name: str):
    """
    Get all the spaces for a given zone.

    Parameters:
        - zone_name (str): The name of the zone.

    Returns:
        - List[Dict[str, Any]]: A list of dictionaries containing the SpaceId, Name, and Description of the spaces.

    Raises:
        - HTTPException: If the zone is not found or there is an error while executing the query.
    """
    try:
        async with DB() as db:
            # First, get the ZoneId for the given zone name
            query = '''
                SELECT [ZoneId]
                FROM [dbo].[Zone]
                WHERE ZoneName = ?;
            '''
            params = (zone_name,)
            zone = await db.execute_query(query, params)

            if not zone:
                raise HTTPException(status_code=404, detail="Zone not found")

            zone_id = zone[0][0]

            # Then, get all spaces for that ZoneId
            query = '''
                SELECT [SpaceId], [Name], [Description]
                FROM [dbo].[Space]
                WHERE ZoneId = ?;
            '''
            params = (zone_id,)
            results = await db.execute_query(query, params)

            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'SpaceId': row[0],
                    'Name': row[1],
                    'Description': row[2]
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/spaces/{SpaceName}")
async def get_space_description(SpaceName: str):
    """
    Get the description of a space for a given SpaceName.

    Parameters:
        - SpaceName (str): The name of the space.

    Returns:
        - List[Dict[str, Any]]: A list of dictionaries containing the SpaceId, Name, and Description of the space.

    Raises:
        - HTTPException: If there is an error while executing the query.
    """
    try:
        async with DB() as db:
            query = '''
                SELECT [SpaceId], [Name], [Description]
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
                    'Name': row[1],
                    'Description': row[2]
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schedules/{SpaceId}/{Day}")
async def get_schedule(SpaceId: int, Day: str):
    """
    Get the schedule for a given SpaceId and Day.

    Parameters:
        - SpaceId (int): The ID of the space.
        - Day (str): The day of the week (e.g., "lunes", "martes", etc.).

    Returns:
        - List[Dict[str, Any]]: A list of dictionaries containing the StartHour and EndHour of the schedule.

    Raises:
        - HTTPException: If there is an error while executing the query.
    """
    today = datetime.now()
    actual_day = today.weekday()  # 0 para lunes, 1 para martes, ..., 6 para domingo
    target_day = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'].index(Day.lower())

    if actual_day <= target_day:
        days_count = target_day - actual_day
    else:
        days_count = 7 - (actual_day - target_day)

    date = today + timedelta(days=days_count)
    final_day = date.strftime('%Y-%m-%d')
    try:
        async with DB() as db:
            query = '''
                SELECT [StartHour], [EndHour]
                FROM [dbo].[Schedule] 
                WHERE [SpaceId] = ? AND [Day] = ? AND [Occupied] = 0;
                '''
            params = (SpaceId, final_day,)
            results = await db.execute_query(query, params)
            formatted_results = []

            for row in results:
                formatted_results.append({
                    'StartHour': row[0],
                    'EndHour': row[1]
                })

            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schedules/{SpaceId}/{Day}/{Hour}")
async def get_schedule_by_hour(SpaceId: int, Day: str, Hour: str):
    today = datetime.now()
    actual_day = today.weekday()  # 0 para lunes, 1 para martes, ..., 6 para domingo
    target_day = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'].index(Day.lower())

    if actual_day <= target_day:
        days_count = target_day - actual_day
    else:
        days_count = 7 - (actual_day - target_day)

    date = today + timedelta(days=days_count)
    final_day = date.strftime('%Y-%m-%d')
    try:
        async with DB() as db:
            query = '''
                SELECT [StartHour], [EndHour]
                FROM [dbo].[Schedule] 
                WHERE [SpaceId] = ? AND [Day] = ? AND [StartHour] = ? AND [Occupied] = 0;
                '''
            params = (SpaceId, final_day, Hour,)
            results = await db.execute_query(query, params)
            formatted_results = []

            for row in results:
                formatted_results.append({
                    'StartHour': row[0],
                    'EndHour': row[1]
                })

            if len(formatted_results) == 0:
                return {"message": "Horario no disponible"}

            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requirements/{SpaceId}")
async def get_space_requirements(SpaceId: int):
    """
    Get the requirements for a given SpaceId.

    Parameters:
        - SpaceId (int): The ID of the space.

    Returns:
        - List[Dict[str, Any]]: A list of dictionaries containing the SpaceId, RequirementId, RequirementName, and MaxQuantity of the requirements.

    Raises:
        - HTTPException: If there is an error while executing the query.
    """
    try:
        async with DB() as db:
            query = "EXEC GetSpaceRequirements @SpaceId = ?"
            params = (SpaceId,)
            results = await db.execute_query(query, params)
            formatted_results = []

            for row in results:
                requirement_id = row[1]
                requirement_name = row[2]
                max_quantity = row[3]

                formatted_results.append({
                    'SpaceId': row[0],
                    'RequirementId': requirement_id,
                    'RequirementName': requirement_name,
                    'MaxQuantity': max_quantity
                })

            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create")
async def create_reservation(res: Reservation):
    """
    Create a reservation in the database.

    Parameters:
        - res (Reservation): The reservation details.

    Returns:
        - Dict[str, str]: A dictionary containing a success message.

    Raises:
        - HTTPException: If there is an error while executing the query.
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
    Create a reservation through the chatbot.

    Parameters:
        - res (ReservationBot): The reservation details.

    Returns:
        - Dict[str, str]: A dictionary containing a success message.

    Raises:
        - HTTPException: If there is an error while executing the query.
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
    dates[1] = "{:02d}:00:00".format(int(dates[1])) # HH:MM:SS

    # Dividir la cadena en dos listas
    numbers_str, values_str = res.user_requirements.split()

    # Convertir las cadenas de números a listas de enteros
    numbers = list(map(int, numbers_str.split(',')))
    values = list(map(int, values_str.split(',')))

    # Iterar sobre las dos listas y formatear los elementos
    result = ""
    for number, value in zip(numbers, values):
        result += f"{number}={value},"

    # Eliminar la coma extra al final
    result = result.rstrip(',')

    print("Resultado:", result)

    try:
        async with DB() as db:
            query = "SELECT [ScheduleId] from dbo.Schedule WHERE [Day] = ? AND [StartHour] = ? AND [SpaceId] = ? AND [Occupied] = 0;"
            params = (dates[0], dates[1], res.space_id)
            results = await db.execute_query(query, params)
            if len(results) == 0:
                raise HTTPException(status_code=404, detail="Schedule not found or already occupied")
            schedule_id = results[0][0]
            return await create_reservation(Reservation(user_id=res.user_id, space_id=res.space_id, schedule_id=int(schedule_id), user_requirements=result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get reservations for a specific user
@router.get("/{user_id}")
async def get_reservations(user_id: int):
    """
    Retrieves reservation details for a given user ID.

    Args:
        user_id (int): The ID of the user.

    Returns:
        list: A list of dictionaries containing reservation details. Each dictionary contains the following keys:
            - 'Day': The date of the reservation in the format 'YYYY-MM-DD'.
            - 'StartHour': The start time of the reservation in the format 'HH:MM'.
            - 'EndHour': The end time of the reservation in the format 'HH:MM'.
            - 'SpaceName': The name of the reserved space.
            - 'SpaceId': The ID of the reserved space.
            - 'RequirementsId': The ID of the reservation requirements.
            - 'RequirementsQuantity': The quantity of reservation requirements.
            - 'GroupCode': The group code associated with the reservation.
    """
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
                    'UserRequirements': row[5],
                    'GroupCode': row[6]
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/")
async def delete_reservation(body: DeleteReservation):
    """
    Deletes a reservation based on the provided group code and user ID.

    Args:
        body (DeleteReservation): An instance of the DeleteReservation model containing the group code and user ID.

    Returns:
        dict: A dictionary with a "message" key indicating the success of the deletion.

    Raises:
        HTTPException: If an error occurs during the deletion process.
    """
    try:
        print(body)
        async with DB() as db:
            query = "EXEC CancelReservation @groupCode = ?, @userId = ?;"
            params = (body.group_code, body.user_id)
            results = await db.execute_query_insert(query, params)
            return {"message": "Reservation deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))