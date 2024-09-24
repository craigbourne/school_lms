# Main module for the LMS application, containing FastAPI app and route definitions.

from typing import List
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from models import User, UserInDB

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
    # Retrieve a user from the database by username.
    for user in users_db:
        if user.username == username:
            return user
    return None

def authenticate_user(username: str, password: str):
    # Authenticate a user based on username and password.
    user = get_user(username)
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user

@app.get("/")
async def home(request: Request):
    # Render the home page (login form).
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
async def register_page(request: Request):
    # Render the registration page.
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...)
):
    # Handle user registration.
    if get_user(username):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username already registered"}
        )
    hashed_password = pwd_context.hash(password)
    user_in_db = UserInDB(username=username, email=email, hashed_password=hashed_password)
    users_db.append(user_in_db)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "message": "User created successfully. Please log in."}
    )

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Handle user login.
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Here we'll add JWT token generation later
    return {"access_token": user.username, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(current_user: User = Depends(oauth2_scheme)):
    # Retrieve the current user's information.
    return current_user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
