from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
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
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: EmailStr = Form(...)
):
    if get_user(username):
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already registered"})
    
    hashed_password = pwd_context.hash(password)
    user_in_db = UserInDB(username=username, email=email, hashed_password=hashed_password)
    users_db.append(user_in_db)
    return templates.TemplateResponse("login.html", {"request": request, "message": "User created successfully. Please log in."})

@app.post("/login")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    # Here we want to eventually validate the username and password
    # For now, we'll just print and redirect back to the home page
    print(f"Login attempt - Username: {form_data.username}, Password: {form_data.password}")
    return templates.TemplateResponse("login.html", {"request": request, "message": f"Login attempt for {form_data.username}"})

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(oauth2_scheme)):
    return current_user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)