from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, Response, Cookie
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import timedelta
from models import UserInDB
from auth import (
    create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES,
    get_user, users_db, authenticate_user, pwd_context, get_password_hash
)
from token_blacklist import add_to_blacklist

app = FastAPI()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Mount a static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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
    email: str = Form(...)
):
    if get_user(username):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username already registered"}
        )
    hashed_password = get_password_hash(password)
    user_in_db = UserInDB(username=username, email=email, hashed_password=hashed_password)
    users_db.append(user_in_db)
    return RedirectResponse(url="/", status_code=303)

@app.post("/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...)):
    print(f"Login attempt for username: {username}")  # Debug print
    user = authenticate_user(username, password)
    if user is None:
        print("Authentication failed")  # Debug print
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    print("Authentication successful")  # Debug print
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    print(f"Access token created: {access_token}")  # Debug print
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token", 
        value=f"Bearer {access_token}", 
        httponly=True,
        max_age=1800,  # 30 minutes
        expires=1800,
        path="/"
    )
    print(f"Setting cookie: access_token=Bearer {access_token}")
    return response

@app.get("/dashboard")
async def dashboard(request: Request, access_token: str = Cookie(None)):
    print("Headers:", request.headers)
    print("Cookies:", request.cookies)
    print("Access Token from Cookie:", access_token)
    
    if not access_token:
        return RedirectResponse(url="/", status_code=303)
    
    try:
        token = access_token.split("Bearer ")[1]
        current_user = get_current_user(token)
        return templates.TemplateResponse("dashboard.html", {"request": request, "user": current_user})
    except Exception as e:
        print(f"Error in dashboard route: {e}")
        return RedirectResponse(url="/", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
