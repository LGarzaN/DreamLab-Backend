from fastapi import FastAPI, HTTPException
import requests
from app.models import ChatRequest
from fastapi_utilities import repeat_at
from app.db import DB
from .routers import reservations, login, chatbot, admin, user
import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from app.functions import create_new_schedules, assign_spaces

app = FastAPI()

app.include_router(reservations.router)
app.include_router(chatbot.router)
app.include_router(login.router)
app.include_router(admin.router)
app.include_router(user.router)

@app.get("/")
async def root():
    return {"message": "V7", "Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    


@app.post("/chat")
async def chat(chat_request: ChatRequest):
    chatbot_url = "https://dreamlabchatbot.azurewebsites.net/chat/"
    data = {
        "session_id": chat_request.session_id,
        "prompt": chat_request.prompt
    }
    response = requests.post(chatbot_url, json=data)
    return response.json()

@app.get("/areas")
async def get_areas():
    try:
        async with DB() as db:
            query = "SELECT * FROM [dbo].[Space]"
            results = await db.execute_query(query)
            formatted_results = []
            print(results)
            for row in results:
                formatted_results.append({
                    'SpaceId': row[0],
                    'SpaceName': row[1],
                    'description': row[3],
                })
            return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
@repeat_at(cron='0 6 * * *')
@retry(stop=stop_after_attempt(5), wait=wait_exponential())
async def schedules():
    await create_new_schedules()
    await assign_spaces()