from fastapi import FastAPI, Response, Depends, Header
import requests
from app.dependencies import check_api_key
from app.models import User, ChatRequest
from app.routers.login import login
from app.db import DB

app = FastAPI(dependencies=[Depends(check_api_key)])
db = DB()

@app.get("/")
async def root():    
    return {"message": "V5"}


@app.post("/chat")
async def chat(chat_request: ChatRequest):
    chatbot_url = "https://dreamlabchatbot.azurewebsites.net/chat/"
    data = {
        "session_id": chat_request.session_id,
        "prompt": chat_request.prompt
    }
    response = requests.post(chatbot_url, json=data)
    return response.json()


# login route
@app.post("/login")
async def auth(user: User, response: Response):
    try:
        if await login(user, db):
            return {"message": "Logged in"}
        else:
            response.status_code = 401
            return {"error": "Unauthorized"}
    except Exception as e:
        response.status_code = 500
        return {"error": str(e)}
    

@app.get("/reservations")
async def get_reservations():
    query = "SELECT * FROM dbo.Reservations"
    results = await db.execute_query(query)
    return results


@app.get("/reservations/{user_id}")
async def get_reservations(user_id: int):
    query = f"SELECT * FROM dbo.Reservations WHERE user_id = {user_id} ORDER BY date DESC"
    results = await db.execute_query(query)
    return results


@app.on_event("shutdown")
async def shutdown_event():
    db.close()