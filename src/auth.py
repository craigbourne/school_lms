from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from models import UserInDB

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "your-secret-key"  # Replace with a real secret key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    async def __call__(self, request: Request, access_token: str = Cookie(None)):
        if not access_token:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return access_token

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token")

# Simulated database
users_db: List[UserInDB] = []

def get_user(username: str) -> Optional[UserInDB]:
    for user in users_db:
        if user.username == username:
            return user
    return None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = get_user(username)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
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

def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    print(f"Token received in get_current_user: {token}")  # Debug print
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        print(f"Decoded username from token: {username}")  # Debug print
        if username is None:
            print("Username is None")  # Debug print
            raise credentials_exception
    except JWTError as exc:
        print(f"JWT decoding error: {exc}")  # Debug print
        raise credentials_exception from exc
    user = get_user(username)
    if user is None:
        print("User not found in database")  # Debug print
        raise credentials_exception
    print(f"User authenticated: {user.username}")  # Debug print
    return user

__all__ = [
    'create_access_token', 
    'get_current_user', 
    'ACCESS_TOKEN_EXPIRE_MINUTES', 
    'get_user', 
    'users_db', 
    'pwd_context', 
    'authenticate_user', 
    'get_password_hash', 
    'verify_password',
    'oauth2_scheme'
]
