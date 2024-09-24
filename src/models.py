# Module containing user-related data models for the LMS application.

from typing import Optional
# pylint: disable=no-name-in-module
from pydantic import BaseModel, EmailStr

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
    # User model for database storage, including hashed password.
    hashed_password: str
