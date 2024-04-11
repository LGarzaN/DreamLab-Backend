from fastapi import APIRouter, Depends, HTTPException
from app.models import User
from app.db import DB
from jose import jwt
from dotenv import load_dotenv
import os

load_dotenv()

db = DB()

router = APIRouter(
    prefix="/login",
    tags=["reservations"]
)

@router.post("/")
async def auth(user: User):
    try: 
        query = "SELECT * FROM [dbo].[User] WHERE Username = ? AND Password = ?"
        params = (user.username, user.password)
        results = await db.execute_query(query, params)

        if len(results) > 0:
            token = jwt.encode({
                "username": user.username, 
                "userId": results[0][0],
                "name": results[0][3],
                }, os.getenv('JWT_SECRET'), algorithm='HS256')
            return {"token": token}
        else:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))