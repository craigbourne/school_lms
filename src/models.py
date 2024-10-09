# Module containing user-related data models for the LMS application.
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from datetime import date, datetime, time, timedelta

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
    @validator('start_time')
    def start_time_must_be_valid(cls, v):
        valid_start_times = [time(hour=h) for h in range(9, 15)]
        if v not in valid_start_times:
            raise ValueError('start time must be on the hour between 9:00 and 14:00')
        return v

    @validator('end_time')
    def end_time_must_be_one_hour_after_start_time(cls, v, values):
        if 'start_time' in values:
            expected_end_time = (
                datetime.combine(date.today(), values['start_time']) + timedelta(hours=1)
            ).time()
            if v != expected_end_time:
                raise ValueError('end time must be exactly one hour after start time')
        return v 

class Lesson(LessonBase):
    id: int

    class Config:
        orm_mode = True

class Timetable(BaseModel):
    id: int
    user_id: int
    week_start: date
    week_end: date
    lessons: List[Lesson] = []  # Default to an empty list

    class Config:
        orm_mode = True

class TimetableCreate(BaseModel):
    user_id: int
    week_start: date
    week_end: date