from app.db import DB
from app.models import Reservation
from uuid import uuid4

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