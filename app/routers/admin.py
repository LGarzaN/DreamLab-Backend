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

            SELECT [User].[Name], [User].[UserName], [Schedule].[Day], [Schedule].[StartHour], [Schedule].[EndHour], [Space].[Name] AS SpaceName
            FROM [dbo].[User]
            INNER JOIN [dbo].[Reservation]
                ON [dbo].[User].[UserId] = [dbo].[Reservation].[UserId]
            INNER JOIN [dbo].[Schedule]
                ON [dbo].[Reservation].[ScheduleId] = [dbo].[Schedule].[ScheduleId]
            INNER JOIN [dbo].[Space]
                ON [dbo].[Reservation].[SpaceId] = [dbo].[Space].[SpaceId]
            WHERE [dbo].[Schedule].[Day] >= CAST(GETDATE() AS Date);


            '''
            results = await db.execute_query(query)

            
            formatted_results = []
            for row in results:
                # Convert date to written format
                day = row[2].day
                month = row[2].strftime('%B')
                year = row[2].year
                weekday = row[2].strftime('%A')
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
                weekday_in_spanish = {
                    'Monday': 'Lunes',
                    'Tuesday': 'Martes',
                    'Wednesday': 'Miércoles',
                    'Thursday': 'Jueves',
                    'Friday': 'Viernes',
                    'Saturday': 'Sábado',
                    'Sunday': 'Domingo'
                }
                formatted_date = f"{day} de {month_in_spanish[month]} {year}"
                formatted_weekday = weekday_in_spanish[weekday]

                formatted_results.append({
                    'nombre': f"{row[0]}",
                    'matricula': f"{row[1]}",
                    'dia': {formatted_weekday},
                    'fecha': {formatted_date},
                    'hora_inicio': f"{row[3].strftime('%H:%M')}",
                    'hora_fin': f"{row[4].strftime('%H:%M')}",
                    "espacio": f"{row[5]}"
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/areas")
async def get_Areas():
    try:
        async with DB() as db:
            query = '''

            SELECT [Name]
            FROM [dbo].[Space]
            


            '''
            results = await db.execute_query(query)

            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'areas': f"{row[0]}"
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#SELECT [Name]
 #               FROM [dbo].[User]
    
  #              SELECT s.Name
   #             FROM Space s
    #            INNER JOIN Reservation r ON s.SpaceId = r.SpaceId;