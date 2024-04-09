from fastapi import FastAPI, Response
import requests
from app.models import User, ChatRequest
from app.db import DB

from .routers import reservations, login

app = FastAPI()

db = DB()

app.include_router(reservations.router)
app.include_router(login.router)

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


@app.on_event("shutdown")
async def shutdown_event():
    db.close()