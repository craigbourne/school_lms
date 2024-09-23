from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: Optional[int] = None
    is_active: bool = True

    class Config:
        orm_mode = True

class UserInDB(User):
    hashed_password: str