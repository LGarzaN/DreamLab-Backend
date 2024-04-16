from fastapi import APIRouter, Depends, HTTPException

from app.db import DB
from app.dependencies import check_api_key

router = APIRouter(
    prefix="/reservations",
    tags=["reservations"],
    dependencies=[Depends(check_api_key)]
)

usrReservations = [
    {
        "user_requirements": "Requirement1",
        "day": "2024-04-09",
        "start_hour": "09:00:00",
        "end_hour": "11:00:00",
        "space_name": "SpaceName1"
    },
    {
        "user_requirements": "Requirement2",
        "day": "2024-04-10",
        "start_hour": "13:00:00",
        "end_hour": "15:00:00",
        "space_name": "SpaceName2"
    },
    {
        "user_requirements": "Requirement3",
        "day": "2024-04-11",
        "start_hour": "10:00:00",
        "end_hour": "12:00:00",
        "space_name": "SpaceName3"
    }
]

adminReservations = [
    {
        "user_id": 1,
        "user_requirements": "Requirement1",
        "day": "2024-04-09",
        "start_hour": "09:00:00",
        "end_hour": "11:00:00",
        "space_name": "SpaceName1"
    },
    {
        "user_id": 2,
        "user_requirements": "Requirement2",
        "day": "2024-04-10",
        "start_hour": "13:00:00",
        "end_hour": "15:00:00",
        "space_name": "SpaceName2"
    },
    {
        "user_id": 3,
        "user_requirements": "Requirement3",
        "day": "2024-04-11",
        "start_hour": "10:00:00",
        "end_hour": "12:00:00",
        "space_name": "SpaceName3"
    }
]

@router.get("/schedule/{area_id}")
async def get_Schedule(area_id: int):
    try:
        async with DB() as db:
            query = "SELECT Day, StartHour, EndHour FROM [dbo].[Schedule] WHERE SpaceId = ? and Occupied = 0;"
            params = (area_id,)
            results = await db.execute_query(query, params)

            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'Day': row[0].strftime('%Y-%m-%d'),
                    'StartHour': row[1].strftime('%H:%M'),
                    'EndHour': row[2].strftime('%H:%M'),
                })
            
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#ADMIN ROUTE
@router.get("/")
async def get_reservations():
    try:
        async with DB() as db:
            query = '''
            SELECT 
            R.user_requirements AS user_requirements,
            S.day AS day,
            S.start_hour AS start_hour,
            S.end_hour AS end_hour,
            SP.name AS space_name
            FROM 
                RESERVATION R
            JOIN 
                SCHEDULES S ON R.schedule_id = S.schedule_id
            JOIN 
                SPACES SP ON R.space_id = SP.space_id
            ORDER BY 
                S.day DESC, S.start_hour DESC
            LIMIT 150;
            '''
            #results = await db.execute_query(query)
            return adminReservations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}")
async def get_reservations(user_id: int):
    try:
        async with DB() as db:
            query = '''
            SELECT 
            R.user_requirements AS user_requirements,
            S.day AS day,
            S.start_hour AS start_hour,
            S.end_hour AS end_hour,
            SP.name AS space_name
            FROM 
                RESERVATION R
            JOIN 
                SCHEDULES S ON R.schedule_id = S.schedule_id
            JOIN 
                SPACES SP ON R.space_id = SP.space_id
            WHERE 
                R.user_id = [your_user_id];
            ORDER BY 
                S.day DESC, S.start_hour DESC;
            '''
            # params = (user_id)
            # results = await db.execute_query(query, params)
            return usrReservations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))