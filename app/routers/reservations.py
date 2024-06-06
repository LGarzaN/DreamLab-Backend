from fastapi import APIRouter, Depends, HTTPException, Header
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
    """
    Retrieves the schedule for a specific area.

    Parameters:
    - area_id (int): The ID of the area.

    Returns:
    - list: A list of dictionaries containing the schedule information. Each dictionary has the following keys:
        - ScheduleId (int): The ID of the schedule.
        - Day (str): The date of the schedule in the format 'YYYY-MM-DD'.
        - StartHour (str): The start time of the schedule in the format 'HH:MM'.
        - EndHour (str): The end time of the schedule in the format 'HH:MM'.

    Raises:
    - HTTPException: If there is an error retrieving the schedule, a 500 status code with the error message is raised.
    """
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
    Create a new reservation.

    Args:
        res (Reservation): The reservation object containing the necessary information.

    Returns:
        dict: A dictionary with a success message if the reservation is created successfully.

    Raises:
        HTTPException: If an error occurs while creating the reservation.
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
    Create a reservation through a chatbot.

    Args:
        res (ReservationBot): The reservation details.

    Returns:
        Reservation: The created reservation.

    Raises:
        HTTPException: If there is an error creating the reservation.
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
    """
    Retrieves reservation details for a given user.

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
            - 'RequirementsQuantity': The quantity of the reservation requirements.
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
    
@router.get("/pending/{user_id}")
async def get_pending_reservations(user_id: int):
    """
    Retrieves the pending reservations for a specific user.

    Parameters:
    - user_id (int): The ID of the user.

    Returns:
    - list: A list of dictionaries containing the formatted pending reservations.
            Each dictionary contains the following keys:
            - 'PendingReservationId': The ID of the pending reservation.
            - 'SpaceId': The ID of the space.
            - 'Day': The day of the reservation in the format 'YYYY-MM-DD'.
            - 'StartHour': The start hour of the reservation in the format 'HH:MM'.
            - 'EndHour': The end hour of the reservation in the format 'HH:MM'.

    Raises:
    - HTTPException: If an error occurs while retrieving the pending reservations.
    """
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
async def delete_reservation(body: DeleteReservation, reservation_type: str = Header(None)):
    """
    Deletes a reservation based on the provided parameters.

    Parameters:
    - body: An instance of the DeleteReservation model, containing the reservation_id and user_id.
    - reservation_type: A string indicating the type of reservation (e.g., "pending").

    Returns:
    - A dictionary with a "message" key indicating the success of the deletion.

    Raises:
    - HTTPException: If an error occurs during the deletion process.
    """
    try:
        async with DB() as db:
            print(reservation_type)
            if reservation_type == "pending":
                query = "UPDATE [dbo].[PendingReservation] SET Deleted = 1 WHERE [PendingReservationId] = ? AND [UserId] = ?;"
                params = (body.reservation_id, body.user_id)
                results = await db.execute_query_insert(query, params)
                return {"message": "Reservation deleted successfully"}
            else:
                query = """
                DECLARE @GroupId INT

                SELECT @GroupId = GroupId FROM ReservationGroup where GroupCode = ?

                UPDATE [dbo].[Reservation] SET Deleted = 1 WHERE GroupId = @GroupId;
                """
                params = (body.group_code,)
                results = await db.execute_query_insert(query, params)
                return {"message": "Reservation deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))