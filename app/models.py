from pydantic import BaseModel

class User(BaseModel):
    username: str = None
    password: str = None
    name: str = None
    role_id: int = 0
    priority: int = 0
    profile_picture: str = None
    tag_id: str = None
    pattern_password: str = None

class ChatRequest(BaseModel):
    session_id: str
    prompt: str

class Reservation(BaseModel):
    user_id: int
    schedule_id: int
    user_requirements: str = None
    space_id: int

class ReservationBot(BaseModel):
    user_id: int    
    schedule: str
    user_requirements: str = None
    space_id: int

class DeleteReservation(BaseModel):
    user_id: int
    group_code: str = None
    reservation_id: int = None