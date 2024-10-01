from auth import (ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_current_user,
    get_user, users_db, authenticate_user, pwd_context, get_password_hash)
from datetime import date, timedelta
from fastapi import FastAPI, Cookie, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models import Lesson, Timetable, TimetableCreate, UserInDB
from token_blacklist import add_to_blacklist
from typing import List

app = FastAPI()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Mount a static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Simulated database for lessons
lessons_db = []

# Database for lessons
timetables_db: List[Timetable] = []

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
    if any(user.username == username for user in users_db):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username already registered"}
        )
    hashed_password = get_password_hash(password)
    new_user = UserInDB(
        id=len(users_db) + 1,  # Simple ID assignment
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    users_db.append(new_user)
    return RedirectResponse(url="/", status_code=303)

# track login attempts
login_attempts = {}

@app.post("/login")
async def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(username, password)
    if user is None:
        # Increment failed login attempts
        login_attempts[username] = login_attempts.get(username, 0) + 1
        
        if login_attempts[username] >= 5:
            # Lock out user after 5 failed attempts
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Account locked. Please contact support."},
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": f"Incorrect username or password. {5 - login_attempts[username]} attempts remaining."},
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Reset login attempts on successful login
    login_attempts.pop(username, None)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token", 
        value=f"Bearer {access_token}", 
        httponly=True,
        max_age=1800,
        expires=1800,
        path="/"
    )
    return response

@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
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

@app.get("/lessons/", response_model=List[Lesson])
async def list_lessons(current_user: UserInDB = Depends(get_current_user)):
    return lessons_db

@app.get("/lessons/{lesson_id}", response_model=Lesson)
async def get_lesson(lesson_id: int, current_user: UserInDB = Depends(get_current_user)):
    for lesson in lessons_db:
        if lesson.id == lesson_id:
            return lesson
    raise HTTPException(status_code=404, detail="Lesson not found")

@app.post("/lessons/", response_model=Lesson)
async def create_lesson(lesson: Lesson, current_user: UserInDB = Depends(get_current_user)):
    # For now, only admins can create lessons
    # Still need to implement role-based access control. Will come back to later
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can create lessons")
    lesson.id = len(lessons_db) + 1  # Simple ID assignment
    lessons_db.append(lesson)
    return lesson

@app.put("/lessons/{lesson_id}", response_model=Lesson)
async def update_lesson(lesson_id: int, updated_lesson: Lesson, current_user: UserInDB = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can update lessons")
    for i, lesson in enumerate(lessons_db):
        if lesson.id == lesson_id:
            updated_lesson.id = lesson_id
            lessons_db[i] = updated_lesson
            return updated_lesson
    raise HTTPException(status_code=404, detail="Lesson not found")

@app.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(lesson_id: int, current_user: UserInDB = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can delete lessons")
    for i, lesson in enumerate(lessons_db):
        if lesson.id == lesson_id:
            lessons_db.pop(i)
            return
    raise HTTPException(status_code=404, detail="Lesson not found")

@app.get("/timetable/{user_id}", response_model=Timetable)
async def get_timetable(user_id: int, current_user: UserInDB = Depends(get_current_user)):
    # Need to fetch actual timetable from database
    # For now, return a dummy timetable
    return Timetable(id=1, user_id=user_id, lessons=lessons_db)

@app.post("/timetables/", response_model=Timetable)
async def create_timetable(timetable: TimetableCreate, current_user: UserInDB = Depends(get_current_user)):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Only administrators and teachers can create timetables")
    
    # Logic to create a timetable
    new_timetable = Timetable(
        id=len(timetables_db) + 1,
        user_id=timetable.user_id,
        week_start=timetable.week_start,
        week_end=timetable.week_end,
        lessons=[]
    )
    timetables_db.append(new_timetable)
    return new_timetable

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return current_user

@app.get("/protected")
async def protected_route(current_user: UserInDB = Depends(get_current_user)):
    return {"message": f"Hello, {current_user.username}! This is a protected route."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
