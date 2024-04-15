from fastapi import APIRouter, HTTPException, Depends
from app.models import User
from app.db import DB
from jose import jwt
from dotenv import load_dotenv
from app.dependencies import check_api_key
import os
import bcrypt


load_dotenv()

router = APIRouter(
    prefix="/login",
    tags=["login"],
    dependencies=[Depends(check_api_key)]
)

@router.post("/")
async def login(user: User):
    try: 
        async with DB() as db:
            query = "SELECT * FROM [dbo].[User] WHERE Username = ?"
            params = (user.username)
            results = await db.execute_query(query, params)

            if bcrypt.checkpw(user.password.encode('utf-8'), results[0][2].encode('utf-8')):
                token = jwt.encode({
                    "username": user.username, 
                    "userId": results[0][0],
                    "name": results[0][3],
                    "role": results[0][4],
                    "priority": results[0][5],
                    "profile picture": results[0][6],
                    }, os.getenv('JWT_SECRET'), algorithm='HS256')
                return {"token": token}
            else:
                raise HTTPException(status_code=401, detail="Unauthorized") 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/create")
async def create_user(user: User):
    try: 
        async with DB() as db:
            hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
            
            query = "INSERT INTO [dbo].[User] (Username, Password, Name, RoleId, Priority, ProfilePicture) VALUES (?, ?, ?, ?, ?, ?);"
            params = (user.username, hashed_password, user.name, user.roleId, user.priority, user.profile_picture)
            results = await db.execute_query_insert(query=query, params=params)
            
            return {"message": "User created successfully", "results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))