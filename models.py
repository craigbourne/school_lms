from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    id: Optional[int] = None
    username: str
    password: str
    email: EmailStr
    is_active: bool = True

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr

class UserInDB(User):
    hashed_password: str