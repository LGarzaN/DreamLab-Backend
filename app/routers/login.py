from fastapi import APIRouter, HTTPException, Depends
from app.models import User
from app.db import DB
import os
from jose import jwt
from dotenv import load_dotenv
from app.dependencies import check_api_key
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
    """
    Authenticates a user by checking their username and password.

    Args:
        user (User): The user object containing the username and password.

    Returns:
        dict: A dictionary containing the authentication token if the user is authenticated.

    Raises:
        HTTPException: If the user is not authenticated or an error occurs during the authentication process.
    """
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
    
@router.post("/pattern")
async def pattern_login(user: User):
    """
    Endpoint for pattern login.

    Parameters:
    - user (User): User object containing the username and pattern password.

    Returns:
    - dict: Dictionary containing the JWT token if the pattern password is correct.

    Raises:
    - HTTPException: If the pattern password is incorrect (status_code=401) or if there is a server error (status_code=500).
    """
    try:
        async with DB() as db:
            query = "SELECT PatternPassword, UserId, Name, RoleId, priority, ProfilePicture from [dbo].[User] WHERE Username = ?"
            params = (user.username)
            results = await db.execute_query(query, params)

            if results[0][0] == user.pattern_password:
                token = jwt.encode({
                    "username": user.username, 
                    "userId": results[0][1],
                    "name": results[0][2],
                    "role": results[0][3],
                    "priority": results[0][4],
                    "profile picture": results[0][5],
                }, os.getenv('JWT_SECRET'), algorithm='HS256')
                return {"token": token}
            else:
                raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/create")
async def create_user(user: User):
    """
    Create a new user in the database.

    Args:
        user (User): The user object containing the user's information.

    Returns:
        dict: A dictionary containing the message and the results of the user creation.

    Raises:
        HTTPException: If there is an error while creating the user.
    """
    try: 
        async with DB() as db:
            hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
            
            query = "INSERT INTO [dbo].[User] (Username, Password, Name, RoleId, Priority, ProfilePicture, TagId, PatternPassword) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
            params = (user.username, hashed_password, user.name, user.role_id, user.priority, user.profile_picture, user.tag_id, user.pattern_password)
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
    """
    Endpoint for logging in with an IoT device using a TagId.

    Args:
        body (TagId): The TagId of the user.

    Returns:
        dict: A dictionary with the message "Logged in" if the login is successful.

    Raises:
        HTTPException: If the login is unsuccessful, an HTTPException with status code 401 (Unauthorized) is raised.
    """
    global login_variable
    async with DB() as db:
        query = f"SELECT * FROM [User] WHERE TagId = '{body.TagId}'"
        results = await db.execute_query(query)
        if len(results) > 0:
            login_variable = True
            return {"message": "Logged in"}
        else:
            raise HTTPException(status_code=401, detail="Unauthorized")
