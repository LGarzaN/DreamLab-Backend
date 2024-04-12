from fastapi import APIRouter, Depends, HTTPException
from app.models import User
from app.db import DB
from jose import jwt
from dotenv import load_dotenv
import os
import bcrypt


load_dotenv()

db = DB()

router = APIRouter(
    prefix="/login",
    tags=["reservations"]
)

@router.post("/")
async def auth(user: User):
    try: 
        query = "SELECT * FROM [dbo].[User] WHERE Username = ?"
        params = (user.username)
        results = await db.execute_query(query, params)

        if bcrypt.checkpw(user.password.encode('utf-8'), results[0][2].encode('utf-8')):
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
    
@router.post("/create")
async def create_user(user: User):
    try: 
        hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
        
        query = "INSERT INTO [dbo].[User] (Username, Password, Name, Priority, ProfilePicture) VALUES (?, ?, ?, ?, ?);"
        params = (user.username, hashed_password, user.name, user.priority, user.profile_picture)
        results = await db.execute_query_insert(query=query, params=params)
        
        return {"message": "User created successfully", "results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))