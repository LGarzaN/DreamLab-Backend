from fastapi import APIRouter, Depends, HTTPException
from app.models import Reservation, DeleteReservation, ReservationBot
from app.db import DB
from app.dependencies import check_api_key
from uuid import uuid4
from app.functions import get_requirements_query
from datetime import datetime, timedelta

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(check_api_key)]
)


@router.get("/reservations")
async def get_Reservations():
    try:
        async with DB() as db:
            query = '''

            SELECT [User].[Name], [User].[UserName], [Schedule].[Day], [Schedule].[StartHour], [Schedule].[EndHour], [Space].[Name], [Space].[SpaceId], [User].[UserId], [ReservationGroup].[GroupCode]
            FROM [dbo].[User]
            INNER JOIN [dbo].[Reservation]
                ON [dbo].[User].[UserId] = [dbo].[Reservation].[UserId]
            INNER JOIN [dbo].[Schedule]
                ON [dbo].[Reservation].[ScheduleId] = [dbo].[Schedule].[ScheduleId]
            INNER JOIN [dbo].[Space]
                ON [dbo].[Reservation].[SpaceId] = [dbo].[Space].[SpaceId]
            INNER JOIN [dbo].[ReservationGroup]
                ON [dbo].[Reservation].[GroupId] = [dbo].[ReservationGroup].[GroupId]
            WHERE [dbo].[Schedule].[Day] >= CAST(GETDATE() AS Date);


            '''
            results = await db.execute_query(query)

            
            formatted_results = []
            for row in results:
                # Convert date to written format
                day = row[2].day
                month = row[2].strftime('%B')
                year = row[2].year
                month_in_spanish = {
                    'January': 'Enero',
                    'February': 'Febrero',
                    'March': 'Marzo',
                    'April': 'Abril',
                    'May': 'Mayo',
                    'June': 'Junio',
                    'July': 'Julio',
                    'August': 'Agosto',
                    'September': 'Septiembre',
                    'October': 'Octubre',
                    'November': 'Noviembre',
                    'December': 'Diciembre'
                }
                formatted_date = f"{day} de {month_in_spanish[month]} {year}"

                formatted_results.append({
                    'Day': f"{row[2]}",
                    'StartHour': f"{row[3].strftime('%H:%M')}",
                    'EndHour': f"{row[4].strftime('%H:%M')}",
                    "SpaceName": f"{row[5]}",
                    "SpaceId": row[6],
                    "GroupCode": f"{row[8]}",
                    'Name': f"{row[0]}",
                    'Matricula': f"{row[1]}",
                    'UserId': row[7],
                    'Fecha': {formatted_date},
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@router.get("/pending")
async def get_Pending():
    try:
        async with DB() as db:
            query = '''

            SELECT 
                pr.[PendingReservationId], 
                pr.[UserId], 
                u.[Name] AS UserName, 
                u.[Username], 
                pr.[SpaceId], 
                sp.[Name] AS SpaceName,
                s.[Day], 
                s.[StartHour], 
                s.[EndHour]
            FROM 
                [dbo].[PendingReservation] pr
            JOIN 
                [dbo].[Schedule] s ON pr.[ScheduleId] = s.[ScheduleId]
            JOIN 
                [dbo].[user] u ON pr.[UserId] = u.[UserId]
            JOIN 
                [dbo].[space] sp ON pr.[SpaceId] = sp.[SpaceId]
            WHERE 
                pr.[DateCreated] >= CAST(GETDATE() AS Date)
                AND pr.[Processed] = 0;

            '''
            results = await db.execute_query(query)

            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "PendingReservationId": row[0],
                    "UserId": row[1],
                    "Name": row[2],
                    "Matricula": row[3],
                    "SpaceId": row[4],
                    "SpaceName": f"{row[5]}",
                    "Day": f"{row[6]}",
                    "StartHour": f"{row[7].strftime('%H:%M')}",
                    "EndHour": f"{row[8].strftime('%H:%M')}"
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))