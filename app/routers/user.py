from fastapi import APIRouter, Depends, HTTPException
from app.db import DB
from app.dependencies import check_api_key
from uuid import uuid4
from app.functions import get_requirements_query
from datetime import datetime, timedelta

router = APIRouter(
    prefix="/user",
    tags=["user"],
    dependencies=[Depends(check_api_key)]
)

@router.get("/statistics/{UserId}")
async def get_statistics(UserId: int):
    try:
        async with DB() as db:
            query = '''
                SELECT [Reservations], [StudyHours], [ExploredAreas]
                FROM [dbo].[Statistic]
                WHERE UserId = ?;
            '''
            params = (UserId,)
            results = await db.execute_query(query, params)

            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'Reservations': row[0],
                    'StudyHours': row[1],
                    'ExploredAreas': row[2]
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))