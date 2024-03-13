from fastapi import FastAPI, Response, status
import requests
from pydantic import BaseModel
from dotenv import load_dotenv
import pyodbc, struct
import os

load_dotenv()

app = FastAPI()

class ChatRequest(BaseModel):
    session_id: str
    prompt: str

class User(BaseModel):
    username: str
    password: str

# connection_string = 'DRIVER={ODBC Driver 17 for SQL Server};Server=tcp:dreamlabdb-server.database.windows.net,1433;Initial Catalog=dreamlabdb;Persist Security Info=False;User ID=luis;Password=Lucman615.;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;'
connection_string = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=dreamlabdb-server.database.windows.net;DATABASE=dreamlabdb;UID=luis;PWD=Lucman615.;'


@app.get("/")
async def root():
    return {"message": "Hello World"}

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
    conn = pyodbc.connect(connection_string) 
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM dbo.Users")
    columns = [column[0] for column in cursor.description]  # Get column names
    results = [dict(zip(columns, row)) for row in cursor.fetchall()] 

    conn.close()

    if results[0]["username"] == user.username and results[0]["password"] == user.password:
        return {"message": "Logged in"}
    else:
        response.status_code = 401
        return {"error": "Unauthorized"}