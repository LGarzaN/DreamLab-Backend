from fastapi import APIRouter, Depends, HTTPException, Header, Query
from app.models import Reservation, DeleteReservation, ReservationBot, ReservationAdmin, AreasFrecuentes
from app.db import DB
from app.dependencies import check_api_key
from uuid import uuid4
from app.functions import get_requirements_query
from datetime import datetime, timedelta
from typing import List 

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
            WHERE 
                [dbo].[Schedule].[Day] >= CAST(GETDATE() AS Date) 
                AND [dbo].[Reservation].[Deleted] = 0


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
    
@router.get("/reservationstype")
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
                formatted_results.append({
                    'Day': f"{row[2]}"
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
                AND pr.[Processed] = 0
                AND pr.[Deleted] = 0;

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
    


@router.post("/create")
async def create_reservation(res: ReservationAdmin):
    """
    Crear una reserva en la base de datos usando el nombre de usuario.

    Formato de userRequirements: "1=1,2=3,4=6"
    donde el primer número es el id del requerimiento y el segundo la cantidad.
    """
    try:
        async with DB() as db:

            user_query = "SELECT UserId FROM [dbo].[User] WHERE Username = ?;"
            user_results = await db.execute_query(user_query, (res.username)) 
            
            if not user_results:
                raise HTTPException(status_code=404, detail="User not found")
            
            user_id = user_results[0][0] 

            reservation_query = "INSERT INTO [dbo].[PendingReservation] (UserId, SpaceId, ScheduleId, UserRequirements) VALUES (?, ?, ?, ?);"
            params = (user_id, res.space_id, res.schedule_id, res.user_requirements)
            results = await db.execute_query_insert(reservation_query, params)
            return {"message": "Reservation created successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str("User not found"))

@router.get("/areasfrecuentesgeneral")
async def get_Pending():
    try:
        async with DB() as db:
            query = '''
            SELECT r.SpaceId, COUNT(*) AS TotalReservations
            FROM [dbo].[Reservation] r
            JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
            WHERE r.SpaceId IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND r.Deleted = 0
            GROUP BY r.SpaceId
            ORDER BY TotalReservations DESC;
                        '''
            results = await db.execute_query(query)

            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    row[0]: row[1],
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estadisticasgeneral")
async def get_pending():
    try:
        async with DB() as db:
            query = '''
            SELECT 
                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                WHERE r.Deleted = 0 
                AND s.Day >= DATEADD(day, -30, GETDATE())
                ) AS NoCanceladas,
                
                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                WHERE r.Deleted = 1 
                AND s.Day >= DATEADD(day, -30, GETDATE())
                ) AS Canceladas,

                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                JOIN [dbo].[User] u ON r.UserId = u.UserId
                WHERE r.Deleted = 0
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND u.Carrera = 'ITC'
                ) AS ITC,

                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                JOIN [dbo].[User] u ON r.UserId = u.UserId
                WHERE r.Deleted = 0
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND u.Carrera = 'ITD'
                ) AS ITD,

                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                JOIN [dbo].[User] u ON r.UserId = u.UserId
                WHERE r.Deleted = 0
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND u.Carrera = 'IRS'
                ) AS IRS;

                
            '''
            results = await db.execute_query(query)
            no_canceladas = results[0][0]
            total_reservas = no_canceladas + results[0][1]
            no_canceladas_porcentaje = round((no_canceladas / total_reservas * 100), 0) if total_reservas > 0 else 0
            canceladas_porcentaje = round((results[0][1] / total_reservas * 100), 0) if total_reservas > 0 else 0
            meta_restante = 100 - no_canceladas
            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "NoCanceladasPorcentaje": no_canceladas_porcentaje,
                })
                formatted_results.append({
                    "CanceladasPorcentaje": canceladas_porcentaje,
                })
                formatted_results.append({
                    "RestanteMeta": meta_restante,
                })
                formatted_results.append({
                    "ActualMeta": no_canceladas,
                })
                formatted_results.append({
                    "ITC": results[0][2],
                })
                formatted_results.append({
                    "ITD": results[0][3],
                })
                formatted_results.append({
                    "IRS": results[0][4],
                })

            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/areasfrecuentesespaciosabiertos")
async def get_Pending():
    try:
        async with DB() as db:
            query = '''
            SELECT r.SpaceId, COUNT(*) AS TotalReservations
            FROM [dbo].[Reservation] r
            JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
            WHERE r.SpaceId IN (1, 2)
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND r.Deleted = 0
            GROUP BY r.SpaceId
            ORDER BY TotalReservations DESC;
                        '''
            results = await db.execute_query(query)

            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    row[0]: row[1],
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/estadisticasespaciosabiertos")
async def get_pending():
    try:
        async with DB() as db:
            query = '''
            SELECT 
                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                WHERE r.Deleted = 0 
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND r.SpaceId IN (1, 2)
                ) AS NoCanceladas,
                
                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                WHERE r.Deleted = 1 
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND r.SpaceId IN (1, 2)
                ) AS Canceladas,

                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                JOIN [dbo].[User] u ON r.UserId = u.UserId
                WHERE r.Deleted = 0
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND r.SpaceId IN (1, 2)
                AND u.Carrera = 'ITC'
                ) AS ITC,

                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                JOIN [dbo].[User] u ON r.UserId = u.UserId
                WHERE r.Deleted = 0
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND u.Carrera = 'ITD'
                AND r.SpaceId IN (1, 2)
                ) AS ITD,

                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                JOIN [dbo].[User] u ON r.UserId = u.UserId
                WHERE r.Deleted = 0
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND u.Carrera = 'IRS'
                AND r.SpaceId IN (1, 2)
                ) AS IRS;

                
            '''
            results = await db.execute_query(query)
            no_canceladas = results[0][0]
            total_reservas = no_canceladas + results[0][1]
            no_canceladas_porcentaje = round((no_canceladas / total_reservas * 100), 0) if total_reservas > 0 else 0
            canceladas_porcentaje = round((results[0][1] / total_reservas * 100), 0) if total_reservas > 0 else 0
            meta_restante = 40 - no_canceladas
            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "NoCanceladasPorcentaje": no_canceladas_porcentaje,
                })
                formatted_results.append({
                    "CanceladasPorcentaje": canceladas_porcentaje,
                })
                formatted_results.append({
                    "RestanteMeta": meta_restante,
                })
                formatted_results.append({
                    "ActualMeta": no_canceladas,
                })
                formatted_results.append({
                    "ITC": results[0][2],
                })
                formatted_results.append({
                    "ITD": results[0][3],
                })
                formatted_results.append({
                    "IRS": results[0][4],
                })

            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/areasfrecuentesgaragevalley")
async def get_Pending():
    try:
        async with DB() as db:
            query = '''
            SELECT r.SpaceId, COUNT(*) AS TotalReservations
            FROM [dbo].[Reservation] r
            JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
            WHERE r.SpaceId IN (3, 4, 5, 6, 7, 8, 9)
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND r.Deleted = 0
            GROUP BY r.SpaceId
            ORDER BY TotalReservations DESC;
                        '''
            results = await db.execute_query(query)

            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    row[0]: row[1],
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/estadisticasgaragevalley")
async def get_pending():
    try:
        async with DB() as db:
            query = '''
            SELECT 
                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                WHERE r.Deleted = 0 
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND r.SpaceId IN (3, 4, 5, 6, 7, 8, 9)
                ) AS NoCanceladas,
                
                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                WHERE r.Deleted = 1 
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND r.SpaceId IN (3, 4, 5, 6, 7, 8, 9)
                ) AS Canceladas,

                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                JOIN [dbo].[User] u ON r.UserId = u.UserId
                WHERE r.Deleted = 0
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND r.SpaceId IN (3, 4, 5, 6, 7, 8, 9)
                AND u.Carrera = 'ITC'
                ) AS ITC,

                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                JOIN [dbo].[User] u ON r.UserId = u.UserId
                WHERE r.Deleted = 0
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND u.Carrera = 'ITD'
                AND r.SpaceId IN (3, 4, 5, 6, 7, 8, 9)
                ) AS ITD,

                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                JOIN [dbo].[User] u ON r.UserId = u.UserId
                WHERE r.Deleted = 0
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND u.Carrera = 'IRS'
                AND r.SpaceId IN (3, 4, 5, 6, 7, 8, 9)
                ) AS IRS;

                
            '''
            results = await db.execute_query(query)
            no_canceladas = results[0][0]
            total_reservas = no_canceladas + results[0][1]
            no_canceladas_porcentaje = round((no_canceladas / total_reservas * 100), 0) if total_reservas > 0 else 0
            canceladas_porcentaje = round((results[0][1] / total_reservas * 100), 0) if total_reservas > 0 else 0
            meta_restante = 30 - no_canceladas
            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "NoCanceladasPorcentaje": no_canceladas_porcentaje,
                })
                formatted_results.append({
                    "CanceladasPorcentaje": canceladas_porcentaje,
                })
                formatted_results.append({
                    "RestanteMeta": meta_restante,
                })
                formatted_results.append({
                    "ActualMeta": no_canceladas,
                })
                formatted_results.append({
                    "ITC": results[0][2],
                })
                formatted_results.append({
                    "ITD": results[0][3],
                })
                formatted_results.append({
                    "IRS": results[0][4],
                })

            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/areasfrecuentesxploracion")
async def get_Pending():
    try:
        async with DB() as db:
            query = '''
            SELECT r.SpaceId, COUNT(*) AS TotalReservations
            FROM [dbo].[Reservation] r
            JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
            WHERE r.SpaceId IN (10, 11, 12, 13, 14, 15)
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND r.Deleted = 0
            GROUP BY r.SpaceId
            ORDER BY TotalReservations DESC;
                        '''
            results = await db.execute_query(query)

            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    row[0]: row[1],
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/estadisticasexploracion")
async def get_pending():
    try:
        async with DB() as db:
            query = '''
            SELECT 
                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                WHERE r.Deleted = 0 
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND r.SpaceId IN (10, 11, 12, 13, 14, 15)
                ) AS NoCanceladas,
                
                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                WHERE r.Deleted = 1 
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND r.SpaceId IN (10, 11, 12, 13, 14, 15)
                ) AS Canceladas,

                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                JOIN [dbo].[User] u ON r.UserId = u.UserId
                WHERE r.Deleted = 0
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND r.SpaceId IN (10, 11, 12, 13, 14, 15)
                AND u.Carrera = 'ITC'
                ) AS ITC,

                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                JOIN [dbo].[User] u ON r.UserId = u.UserId
                WHERE r.Deleted = 0
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND u.Carrera = 'ITD'
                AND r.SpaceId IN (10, 11, 12, 13, 14, 15)
                ) AS ITD,

                (SELECT COUNT(*) 
                FROM [dbo].[Reservation] r
                JOIN [dbo].[Schedule] s ON r.ScheduleId = s.ScheduleId
                JOIN [dbo].[User] u ON r.UserId = u.UserId
                WHERE r.Deleted = 0
                AND s.Day >= DATEADD(day, -30, GETDATE())
                AND u.Carrera = 'IRS'
                AND r.SpaceId IN (10, 11, 12, 13, 14, 15)
                ) AS IRS;

                
            '''
            results = await db.execute_query(query)
            no_canceladas = results[0][0]
            total_reservas = no_canceladas + results[0][1]
            no_canceladas_porcentaje = round((no_canceladas / total_reservas * 100), 0) if total_reservas > 0 else 0
            canceladas_porcentaje = round((results[0][1] / total_reservas * 100), 0) if total_reservas > 0 else 0
            meta_restante = 30 - no_canceladas
            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "NoCanceladasPorcentaje": no_canceladas_porcentaje,
                })
                formatted_results.append({
                    "CanceladasPorcentaje": canceladas_porcentaje,
                })
                formatted_results.append({
                    "RestanteMeta": meta_restante,
                })
                formatted_results.append({
                    "ActualMeta": no_canceladas,
                })
                formatted_results.append({
                    "ITC": results[0][2],
                })
                formatted_results.append({
                    "ITD": results[0][3],
                })
                formatted_results.append({
                    "IRS": results[0][4],
                })

            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



















@router.get("/infotablas")
async def get_pending():
    try:
        async with DB() as db:
            query = '''
            SELECT * FROM [dbo].[User]
            '''
            results = await db.execute_query(query)
            
            # Si results es una lista de tuplas, se necesita acceder a los nombres de las columnas desde el primer resultado
            if results:
                columns_query = '''
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'User'
                '''
                columns_result = await db.execute_query(columns_query)
                columns = [column[0] for column in columns_result]

                # Convertir los resultados a una lista de diccionarios
                formatted_results = [dict(zip(columns, row)) for row in results]
            else:
                formatted_results = []

            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))