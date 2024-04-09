from fastapi import APIRouter, Depends, HTTPException
from app.models import User
from app.db import DB

db = DB()

router = APIRouter(
    prefix="/login",
    tags=["reservations"]
)

@router.post("/")
async def auth(user: User):
    try: 
        query = "SELECT * FROM dbo.Users WHERE username = ? AND password = ?"
        params = (user.username, user.password)
        results = await db.execute_query(query, params)

        if len(results) > 0:
            return {"message": "Logged in"}
        else:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))