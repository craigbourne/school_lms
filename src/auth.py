# Standard library imports
from datetime import datetime, timedelta
from typing import List, Optional

# FastAPI and related imports
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Third-party imports for JWT handling, hashing, & data validation 
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

# The secret key used for JWT encoding and decoding
SECRET_KEY = "your-secret-key"  # Replace with a real secret key in production

# The algorithm used for JWT encoding and decoding
# HS256 is a common choice for JWT
ALGORITHM = "HS256"

# The number of minutes after which an access token will expire
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 password flow config, specifying the token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic models
# Pydantic model representing a user in the database
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

# Pydantic model representing a JWT token
class Token(BaseModel):
    access_token: str
    token_type: str

# Pydantic model representing the data stored in a JWT token
class TokenData(BaseModel):
    username: Optional[str] = None

# Authentication functions
# Verifies a plain password against a hashed password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Authenticates a user based on username and password.
# Returns the user if authentication is successful, False otherwise
def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Creates a JWT access token with the given data and expiration time
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Decodes and validates a JWT access token
# Returns the username if the token is valid, raises an exception otherwise
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

# Retrieves a user from the database by username
# Returns the user if found, None otherwise
def get_user(username: str) -> Optional[UserInDB]:
    for user in users_db:
        if user.username == username:
            return user
    return None

# In-memory user database
# In a production environment, this would be replaced with a proper database
users_db = []
