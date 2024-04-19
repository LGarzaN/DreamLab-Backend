from pydantic import BaseModel

class User(BaseModel):
    username: str = None
    password: str = None
    name: str = None
    roleId: int = 0
    priority: int = 0
    profile_picture: str = None

class ChatRequest(BaseModel):
    session_id: str
    prompt: str

class Reservation(BaseModel):
    user_id: int
    schedule_id: int
    user_requirements: str = None
    space_id: int

class DeleteReservation(BaseModel):
    user_id: int
    group_code: str