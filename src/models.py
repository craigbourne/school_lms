# Module containing user-related data models for the LMS application.

from typing import Optional, List
# pylint: disable=no-name-in-module
from pydantic import BaseModel, EmailStr
from datetime import datetime, time

class UserBase(BaseModel):
    # Base user model containing common attributes.
    username: str
    email: EmailStr

class UserCreate(UserBase):
    # User model for creating a new user, including password.
    password: str

class User(UserBase):
    # User model with additional attributes for authenticated users.
    id: Optional[int] = None
    is_active: bool = True

    class Config:
        # Pydantic configuration for the User model.
        orm_mode = True

class UserInDB(User):
    hashed_password: str

class UserInDB(BaseModel):
    # User model for database storage, including hashed password.
    id: Optional[int] = None
    username: str
    email: EmailStr
    hashed_password: str
    role: str = "student"  # default role, can be "admin", "teacher", etc.

    class Config:
        orm_mode = True

class Lesson(BaseModel):
    id: int
    subject: str
    teacher: str
    classroom: str
    day_of_week: str  # e.g., "Monday", "Tuesday", etc.
    start_time: time
    end_time: time

class Timetable(BaseModel):
    id: int
    user_id: int  # This can be a student's or teacher's ID
    lessons: List[Lesson]
