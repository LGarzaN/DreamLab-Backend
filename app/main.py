from fastapi import FastAPI, HTTPException
import requests
from app.models import ChatRequest
from fastapi_utilities import repeat_at
from app.db import DB
from .routers import reservations, login, chatbot
import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

app = FastAPI()

app.include_router(reservations.router)
app.include_router(chatbot.router)
app.include_router(login.router)

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
    try:
        hours = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00"]
        today = (datetime.datetime.now().strftime("%Y-%m-%d"))
        new_day = datetime.datetime.now() + datetime.timedelta(days=5)
        
        async with DB() as db:
            delete_query = "DELETE FROM [dbo].[Schedule] WHERE Day < ? and Occupied = 0;"
            delete_params = (today,)
            await db.execute_query_insert(query=delete_query, params=delete_params)
            print("Deleted unused schedules from yesterday")

            if new_day.weekday() == 5 or new_day.weekday() == 6:
                print("It's the weekend, no schedules will be added")
                return
            
            new_day = new_day.strftime("%Y-%m-%d")

            string_query = ""
            for i in range(1, 16):
                for j in range(len(hours) -1):
                    string_query += f"\nINSERT INTO [dbo].[Schedule] (SpaceId, Day, StartHour, EndHour, Occupied) VALUES ({i}, '{new_day}', '{hours[j]}', '{hours[j+1]}', 0);"
                string_query += "\n"

            await db.execute_query_insert(query=string_query)
            print("Added new schedules for all rooms for day " + new_day)


    except Exception as e:
        print(str(e))
        raise e