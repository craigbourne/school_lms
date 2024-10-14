# Module containing user-related data models for the LMS application.
from datetime import date, datetime, time, timedelta
from typing import List, Optional

from pydantic import BaseModel, EmailStr, validator

# Decorator function to convert Pydantic models to form data
# Allows Pydantic models to be used with FastAPI's Form class.]
def form_body(cls):
    async def as_form(**data):
        return cls(**data)
    return as_form

# Base model for user data
# Contains common fields for all user-related models
class UserBase(BaseModel):
    username: str
    email: EmailStr

# Model for user registration data
# Includes all fields necessary for creating a new user account
class RegisterModel(BaseModel):
    username: str
    password: str
    email: str
    role: str
    year_group: Optional[int] = None

# Base model for lesson data
# Contains common fields for all lesson-related models
class LessonBase(BaseModel):
    subject: str
    teacher: str
    classroom: str
    day_of_week: str
    start_time: time
    end_time: time
    year_group: int

# Model representing a complete lesson, including its unique identifier
# Inherits from LessonBase and adds an id field
class Lesson(LessonBase):
    id: int

    class Config:
        orm_mode = True

# Model for creating a new lesson.
# Includes validators to ensure the start and end times are valid
# pylint: disable=no-self-argument
class LessonCreate(LessonBase):
    # Validates start time is on the hour between 9:00 & 14:00
    @validator('start_time')
    def start_time_must_be_valid(cls, v):
        valid_start_times = [time(hour=h) for h in range(9, 15)]
        if v not in valid_start_times:
            raise ValueError(
              'start time must be on the hour between 9:00 and 14:00'
            )
        return v

    # Validates end time is exactly one hour after the start time
    @validator('end_time')
    def end_time_must_be_one_hour_after_start_time(cls, v, values):
        if 'start_time' in values:
            expected_end_time = (
                datetime.combine(date.today(),
                values['start_time']) + timedelta(hours=1)
            ).time()
            if v != expected_end_time:
                raise ValueError(
                  'end time must be exactly one hour after start time'
                )
        return v

# Model for editing an existing lesson
# Includes fields that can be modified when updating a lesson
class LessonEditModel(BaseModel):
    subject: str
    classroom: str
    day_of_week: str
    start_time: str
    year_group: int

# Model for adding a new lesson.
# Similar to LessonEditModel, but used specifically for adding new lessons
class LessonAddModel(BaseModel):
    subject: str
    classroom: str
    day_of_week: str
    start_time: str
    year_group: int

# Model representing a complete timetable
# Includes a list of lessons and metadata about the timetable
class Timetable(BaseModel):
    id: int
    user_id: int
    week_start: date
    week_end: date
    lessons: List[Lesson] = []  # Default to an empty list

    class Config:
        orm_mode = True

# Model for creating a new timetable
# Includes the necessary fields to initialize a new timetable
class TimetableCreate(BaseModel):
    user_id: int
    week_start: date
    week_end: date
