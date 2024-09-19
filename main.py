from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import EmailStr
from typing import List
from models import User, UserCreate, UserInDB

app = FastAPI()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Mount a static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Simulated database (replace with actual database later)
users_db: List[UserInDB] = []

def get_user(username: str):
    for user in users_db:
        if user.username == username:
            return user

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.post("/register")
async def register(user: UserCreate):
    if get_user(user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = pwd_context.hash(user.password)
    user_in_db = UserInDB(**user.dict(), hashed_password=hashed_password)
    users_db.append(user_in_db)
    return {"message": "User created successfully"}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Here we want to eventually validate the username and password
    # For now, we'll just print and redirect back to the home page
    print(f"Login attempt - Username: {form_data.username}, Password: {form_data.password}")
    return {"access_token": form_data.username, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(oauth2_scheme)):
    return current_user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)