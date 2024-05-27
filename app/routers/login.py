from fastapi import APIRouter, HTTPException, Depends
from app.models import User
from app.db import DB
from jose import jwt
from dotenv import load_dotenv
from app.dependencies import check_api_key
import os
import bcrypt
import time
from pydantic import BaseModel


load_dotenv()

login_variable = False

router = APIRouter(
    prefix="/login",
    tags=["login"]
    # dependencies=[Depends(check_api_key)]
)

@router.post("/")
async def login(user: User):
    try: 
        async with DB() as db:
            query = "EXEC SearchUser @p_Username = ?;"
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
            
            query = "INSERT INTO [dbo].[User] (Username, Password, Name, RoleId, Priority, ProfilePicture, TagId, PatternPassword) VALUES (?, ?, ?, ?, ?, ?, '', '');"
            params = (user.username, hashed_password, user.name, user.roleId, user.priority, user.profile_picture)
            results = await db.execute_query_insert(query=query, params=params)
            
            return {"message": "User created successfully", "results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/id")
def id_login():
    global login_variable
    print("Waiting for login")
    while login_variable == False:
        time.sleep(1)
    login_variable = False
    return {"message": "Logged in"}


class TagId(BaseModel):
    TagId: str

@router.post("/id/iot")
async def id_login_iot(body: TagId):
    global login_variable
    async with DB() as db:
        query = f"SELECT * FROM [User] WHERE TagId = '{body.TagId}'"
        results = await db.execute_query(query)
        if len(results) > 0:
            login_variable = True
            return {"message": "Logged in"}
        else:
            raise HTTPException(status_code=401, detail="Unauthorized")
