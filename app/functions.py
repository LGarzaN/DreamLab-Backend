from app.db import DB
from app.models import Reservation
from uuid import uuid4
import datetime
from queue import PriorityQueue
import os

def get_requirements_query(reqs : str):
    query = "\n"
    arr = reqs.split(",")
    print(arr)

    for i in arr:
        arr2 = i.split("=")
        query += f"INSERT INTO [dbo].[UserRequirements] (GroupId, RequirementId, Quantity) VALUES (@GroupID, {arr2[0]}, {arr2[1]});\n"
    return query

async def create_confirmed_reservation(res: Reservation):
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
        print(e)

async def create_new_schedules():
        try:
            hours = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00"]
            today = (datetime.datetime.now().strftime("%Y-%m-%d"))
            new_day = datetime.datetime.now() + datetime.timedelta(days=5)
            
            async with DB() as db:
                delete_query = "DELETE FROM [dbo].[Schedule] WHERE Day < ? and Occupied = 0;"
                delete_params = (today,)
                await db.execute_query_insert(query=delete_query, params=delete_params)

                if new_day.weekday() == 5 or new_day.weekday() == 6:
                    return
                new_day = new_day.strftime("%Y-%m-%d")

                string_query = ""
                for i in range(1, 16):
                    for j in range(len(hours) -1):
                        string_query += f"\nINSERT INTO [dbo].[Schedule] (SpaceId, Day, StartHour, EndHour, Occupied) VALUES ({i}, '{new_day}', '{hours[j]}', '{hours[j+1]}', 0);"
                    string_query += "\n"
                await db.execute_query_insert(query=string_query)
        except Exception as e:
            print(str(e))
            raise e
        
async def assign_spaces():
    try:
        async with DB() as db:
            query = """
            SELECT 
                PR.PendingReservationId, U.UserId, PR.ScheduleId, PR.UserRequirements, PR.SpaceId, PR.DateCreated, U.[Priority]
            FROM 
                [dbo].[PendingReservation] as PR JOIN [dbo].[User] as U on PR.Userid = U.UserId
            WHERE 
                Deleted = 0 and Processed = 0 
            ORDER BY 
                DateCreated ASC
            """
            results = await db.execute_query(query)
            # check for duplicate schedule id in results
            requests = {}
            update_query = ""
            for row in results:
                update_query += f"UPDATE [dbo].[PendingReservation] SET Processed = 1 WHERE PendingReservationId = {row[0]};\n"
                if row[2] not in requests:
                    requests[row[2]] = PriorityQueue()
                requests[row[2]].put((row[6], row))
            
            for key in requests:
                top = requests[key].get()[1]
                res = Reservation(user_id=top[1], space_id=top[4], schedule_id=key, user_requirements=top[3])
                await create_confirmed_reservation(res)
            
            await db.execute_query_insert(query=update_query)
    except Exception as e:
        print(str(e))
        raise e
    
async def sign_jwt(dict):
    token = jwt.encode(dict, os.getenv('JWT_SECRET'), algorithm='HS256')
    return token