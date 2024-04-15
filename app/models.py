from pydantic import BaseModel

class User(BaseModel):
    username: str
    password: str
    name: str = None
    roleId: int = 0
    priority: int = 0
    profile_picture: str = None

class ChatRequest(BaseModel):
    session_id: str
    prompt: str