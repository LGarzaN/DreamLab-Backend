from pydantic import BaseModel

class User(BaseModel):
    username: str
    password: str
    #optional fields
    name: str = None
    priority: int = 0
    profile_picture: str = None

class ChatRequest(BaseModel):
    session_id: str
    prompt: str