# Module containing user-related data models for the LMS application.
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date, time

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserInDB(UserBase):
    id: int
    hashed_password: str
    role: str = "student"
    year_group: Optional[int] = None
    subjects: Optional[List[str]] = None

    class Config:
        orm_mode = True

class LessonBase(BaseModel):
    subject: str
    teacher: str
    classroom: str
    day_of_week: str
    start_time: time
    end_time: time
    year_group: int

class LessonCreate(LessonBase):
    pass

class Lesson(LessonBase):
    id: int

    class Config:
        orm_mode = True

class Timetable(BaseModel):
    id: int
    user_id: int
    week_start: date
    week_end: date
    lessons: List[Lesson]

    class Config:
        orm_mode = True

class TimetableCreate(BaseModel):
    user_id: int
    week_start: date
    week_end: date