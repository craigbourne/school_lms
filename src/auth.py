from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

SECRET_KEY = "your-secret-key"  # Replace with a real secret key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserInDB(BaseModel):
    id: int
    username: str
    email: EmailStr
    hashed_password: str
    role: str = "student"
    year_group: Optional[int] = None
    subjects: Optional[List[str]] = None

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Invalid token"
            )
        return username
    except JWTError as exc:
        raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Invalid token"
            ) from exc

def get_user(username: str) -> Optional[UserInDB]:
    for user in users_db:
        if user.username == username:
            return user
    return None

users_db = []
