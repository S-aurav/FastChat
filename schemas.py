from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserProfile(BaseModel):
    username: str
    about: str
    profile_picture: str

class MessageCreate(BaseModel):
    receiver_username: str
    content: str

class MessageResponse(BaseModel):
    sender: str
    content: str
    timestamp: str