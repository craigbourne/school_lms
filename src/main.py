from auth import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, create_access_token, decode_access_token, get_current_user, SECRET_KEY, Token
from datetime import date, datetime, time, timedelta
from fastapi import FastAPI, Cookie, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from models import UserInDB, Lesson, LessonCreate, Timetable, TimetableCreate
from passlib.context import CryptContext
import random
from token_blacklist import add_to_blacklist
from typing import List

app = FastAPI()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Mount a static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str):
    for user in users_db:
        if user.username == username:
            return user
    return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    scheme, _, param = token.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication scheme")
    
    try:
        payload = jwt.decode(param, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user = get_user(username)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# track login attempts
login_attempts = {}

# Simulated database for lessons
lessons_db = []

# Database for lessons
timetables_db: List[Timetable] = []

# Mock data
mock_lessons = [
    Lesson(id=1, subject="Math", teacher="Mr. Smith", classroom="Room 101", day_of_week="Monday", start_time=datetime.strptime("09:00", "%H:%M").time(), end_time=datetime.strptime("10:00", "%H:%M").time(), year_group=7),
    Lesson(id=2, subject="English", teacher="Ms. Johnson", classroom="Room 102", day_of_week="Monday", start_time=datetime.strptime("10:30", "%H:%M").time(), end_time=datetime.strptime("11:30", "%H:%M").time(), year_group=8),
    Lesson(id=3, subject="Science", teacher="Dr. Brown", classroom="Lab 1", day_of_week="Tuesday", start_time=datetime.strptime("09:00", "%H:%M").time(), end_time=datetime.strptime("10:30", "%H:%M").time(), year_group=9),
]

mock_timetable = Timetable(
    id=1,
    user_id=1,
    week_start=date(2023, 5, 1),
    week_end=date(2023, 5, 7),
    lessons=[
        Lesson(id=1, subject="Math", teacher="Mr. Smith", classroom="Room 101", day_of_week="Monday", start_time=time(9, 0), end_time=time(10, 0), year_group=7),
        Lesson(id=2, subject="English", teacher="Ms. Johnson", classroom="Room 102", day_of_week="Monday", start_time=time(10, 30), end_time=time(11, 30), year_group=8),
    ]
)

def create_mock_teachers():
    subjects = ["Math", "English", "Science", "History", "Geography", "Art", "Music", "Physical Education"]
    teachers = []
    for i in range(2):
        teacher_data = {
            "id": i + 1,
            "username": f"teacher{i+1}",
            "email": f"teacher{i+1}@school.com",
            "hashed_password": get_password_hash("password"),  # Use a common password for testing
            "role": "teacher",
            "subjects": random.sample(subjects, 2)
        }
        teacher = UserInDB(**teacher_data)
        teachers.append(teacher)
    return teachers

def create_mock_students():
    students = []
    for i in range(2):
        student_data = {
            "id": i + 3,
            "username": f"student{i+1}",
            "email": f"student{i+1}@school.com",
            "hashed_password": get_password_hash("password"),
            "role": "student",
            "year_group": random.randint(7, 11)
        }
        student = UserInDB(**student_data)
        students.append(student)
    return students

def create_mock_lessons():
    teachers = create_mock_teachers()
    lessons = []
    for i in range(10):  # Create 10 lessons
        teacher = random.choice(teachers)
        subject = random.choice(teacher.subjects)
        lessons.append(Lesson(
            id=i + 1,
            subject=subject,
            teacher=teacher.username,
            classroom=f"Room {random.randint(101, 120)}",
            day_of_week=random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
            start_time=time(hour=random.randint(9, 15)),
            end_time=time(hour=random.randint(10, 16)),
            year_group=random.randint(7, 11)
        ))
        print(f"Created lesson: {subject} by {teacher.username}")
    return lessons

def create_mock_timetables():
    users = create_mock_teachers() + create_mock_students()
    lessons = create_mock_lessons()
    timetables = []
    for user in users:
        if user.role == "student":
            user_lessons = [lesson for lesson in lessons if lesson.year_group == user.year_group]
        elif user.role == "teacher":
            user_lessons = [lesson for lesson in lessons if lesson.teacher == user.username]
        else:  # admin sees all lessons
            user_lessons = lessons
        
        timetable = Timetable(
            id=len(timetables) + 1,
            user_id=user.id,
            week_start=date.today() - timedelta(days=date.today().weekday()),
            week_end=date.today() + timedelta(days=6),
            lessons=user_lessons
        )
        timetables.append(timetable)
    return timetables

# Initialize mock data
users_db = create_mock_teachers() + create_mock_students()
lessons_db = create_mock_lessons()
timetables_db = create_mock_timetables()

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

from datetime import date, timedelta

@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    role: str = Form(...)
):
    if role not in ["admin", "teacher", "student"]:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Invalid role"}
        )
    
    if any(user.username == username for user in users_db):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username already registered"}
        )
    
    hashed_password = get_password_hash(password)
    new_user = UserInDB(
        id=len(users_db) + 1,
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role
    )
    users_db.append(new_user)

    # Create a timetable for the new user
    new_timetable = Timetable(
        id=len(timetables_db) + 1,
        user_id=new_user.id,
        week_start=date.today() - timedelta(days=date.today().weekday()),
        week_end=date.today() + timedelta(days=6),
        lessons=lessons_db.copy()  # New users see all lessons initially
    )
    timetables_db.append(new_timetable)

    return RedirectResponse(url="/", status_code=303)

@app.post("/login")
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    token_response = await login_for_access_token(form_data)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token_response['access_token']}",
        httponly=True,
        max_age=1800,
        expires=1800,
    )
    return response

@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response

@app.get("/dashboard")
async def dashboard(request: Request, current_user: UserInDB = Depends(get_current_user)):
    user_timetable = next((t for t in timetables_db if t.user_id == current_user.id), None)
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": current_user, "timetable": user_timetable})

@app.get("/lessons/")
async def list_lessons(request: Request, current_user: UserInDB = Depends(get_current_user)):
    if current_user.role in ['admin', 'teacher']:
        visible_lessons = lessons_db
    else:
        user_timetable = next((t for t in timetables_db if t.user_id == current_user.id), None)
        visible_lessons = user_timetable.lessons if user_timetable else []
    
    return templates.TemplateResponse("lesson_list.html", {"request": request, "lessons": visible_lessons, "current_user": current_user})

@app.get("/lessons/{lesson_id}", response_model=Lesson)
async def get_lesson(lesson_id: int, current_user: UserInDB = Depends(get_current_user)):
    for lesson in lessons_db:
        if lesson.id == lesson_id:
            return lesson
    raise HTTPException(status_code=404, detail="Lesson not found")

@app.post("/lessons/", response_model=Lesson)
async def create_lesson(lesson: LessonCreate, current_user: UserInDB = Depends(get_current_user)):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Only administrators and teachers can create lessons")
    
    new_lesson = Lesson(id=len(lessons_db) + 1, **lesson.dict())
    lessons_db.append(new_lesson)
    return new_lesson

@app.put("/lessons/{lesson_id}", response_model=Lesson)
async def update_lesson(lesson_id: int, updated_lesson: LessonCreate, current_user: UserInDB = Depends(get_current_user)):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Only administrators and teachers can update lessons")
    
    for i, lesson in enumerate(lessons_db):
        if lesson.id == lesson_id:
            updated_lesson_dict = updated_lesson.dict()
            updated_lesson_dict['id'] = lesson_id
            lessons_db[i] = Lesson(**updated_lesson_dict)
            # Update lesson in timetable
            for timetable in timetables_db:
                for j, timetable_lesson in enumerate(timetable.lessons):
                    if timetable_lesson.id == lesson_id:
                        timetable.lessons[j] = lessons_db[i]
            return lessons_db[i]
    raise HTTPException(status_code=404, detail="Lesson not found")

@app.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(lesson_id: int, current_user: UserInDB = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can delete lessons")
    
    for i, lesson in enumerate(lessons_db):
        if lesson.id == lesson_id:
            lessons_db.pop(i)
            # Remove lesson from timetables
            for timetable in timetables_db:
                timetable.lessons = [l for l in timetable.lessons if l.id != lesson_id]
            return
    raise HTTPException(status_code=404, detail="Lesson not found")

@app.get("/lessons/add/")
async def lesson_add_form(request: Request, current_user: UserInDB = Depends(get_current_user)):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Only administrators and teachers can add lessons")
    return templates.TemplateResponse("lesson_add.html", {"request": request})

@app.post("/lessons/add/")
async def lesson_add(
    request: Request,
    subject: str = Form(...),
    teacher: str = Form(...),
    classroom: str = Form(...),
    day_of_week: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    timetable_id: int = Form(...),
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Only administrators and teachers can add lessons")
    
    # Convert time strings to time objects
    start_time_obj = datetime.strptime(start_time, "%H:%M").time()
    end_time_obj = datetime.strptime(end_time, "%H:%M").time()
    
    new_lesson = LessonCreate(
        subject=subject,
        teacher=teacher,
        classroom=classroom,
        day_of_week=day_of_week,
        start_time=start_time_obj,
        end_time=end_time_obj
    )
    
    created_lesson = await create_lesson(new_lesson, timetable_id, current_user)
    return RedirectResponse(url="/lessons/", status_code=303)

@app.get("/lessons/{lesson_id}/edit")
async def lesson_edit_form(lesson_id: int, request: Request, current_user: UserInDB = Depends(get_current_user)):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Only administrators and teachers can edit lessons")
    
    lesson = next((lesson for lesson in lessons_db if lesson.id == lesson_id), None)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    return templates.TemplateResponse("lesson_edit.html", {"request": request, "lesson": lesson})

@app.post("/lessons/{lesson_id}/edit")
async def lesson_edit(
    lesson_id: int,
    request: Request,
    subject: str = Form(...),
    teacher: str = Form(...),
    classroom: str = Form(...),
    day_of_week: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Only administrators and teachers can edit lessons")
    
    # Convert time strings to time objects
    start_time_obj = datetime.strptime(start_time, "%H:%M").time()
    end_time_obj = datetime.strptime(end_time, "%H:%M").time()
    
    updated_lesson = LessonCreate(
        subject=subject,
        teacher=teacher,
        classroom=classroom,
        day_of_week=day_of_week,
        start_time=start_time_obj,
        end_time=end_time_obj
    )
    
    # Find the lesson in the database and update it
    for i, lesson in enumerate(lessons_db):
        if lesson.id == lesson_id:
            lessons_db[i] = Lesson(id=lesson_id, **updated_lesson.dict())
            # Update the lesson in all timetables
            for timetable in timetables_db:
                for j, timetable_lesson in enumerate(timetable.lessons):
                    if timetable_lesson.id == lesson_id:
                        timetable.lessons[j] = lessons_db[i]
            return RedirectResponse(url="/lessons/", status_code=303)
    
    raise HTTPException(status_code=404, detail="Lesson not found")

@app.post("/lessons/{lesson_id}/delete")
async def lesson_delete(lesson_id: int, current_user: UserInDB = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can delete lessons")
    
    for i, lesson in enumerate(lessons_db):
        if lesson.id == lesson_id:
            lessons_db.pop(i)
            # Remove lesson from timetables
            for timetable in timetables_db:
                timetable.lessons = [l for l in timetable.lessons if l.id != lesson_id]
            return RedirectResponse(url="/lessons/", status_code=303)
    
    raise HTTPException(status_code=404, detail="Lesson not found")

from datetime import date, timedelta

@app.get("/timetable/")
async def view_timetable(request: Request, week_start: date = None, current_user: UserInDB = Depends(get_current_user)):
    if week_start is None:
        # If no week is specified, use the current week
        week_start = date.today() - timedelta(days=date.today().weekday())
    
    week_end = week_start + timedelta(days=6)
    
    # Find the timetable for the current user and specified week
    timetable = next((t for t in timetables_db if t.user_id == current_user.id), None)
    
    if not timetable:
        # If no timetable exists, create an empty one
        timetable = Timetable(id=len(timetables_db) + 1, user_id=current_user.id, week_start=week_start, week_end=week_end, lessons=[])
        timetables_db.append(timetable)
    
    return templates.TemplateResponse("timetable_view.html", {"request": request, "timetable": timetable, "current_user": current_user})

@app.get("/timetable/{user_id}", response_model=Timetable)
async def get_timetable(user_id: int, current_user: UserInDB = Depends(get_current_user)):
    # Need to fetch actual timetable from database
    # For now, return a dummy timetable
    return Timetable(id=1, user_id=user_id, lessons=lessons_db)

@app.get("/timetables/{user_id}/{week_start}", response_model=Timetable)
async def get_weekly_timetable(user_id: int, week_start: date, current_user: UserInDB = Depends(get_current_user)):
    print(f"Searching for timetable: user_id={user_id}, week_start={week_start}")
    print(f"Current timetables in db: {timetables_db}")
    
    if current_user.role == "student" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Students can only view their own timetable")
    
    timetable = next((t for t in timetables_db if t.user_id == user_id and t.week_start == week_start), None)
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    
    return timetable

@app.get("/timetables/{user_id}", response_model=Timetable)
async def get_timetable(user_id: int, week_start: date, current_user: UserInDB = Depends(get_current_user)):
    try:
        if current_user.id != user_id and current_user.role not in ["admin", "teacher"]:
            raise HTTPException(status_code=403, detail="You can only view your own timetable")
        
        timetable = next((t for t in timetables_db if t.user_id == user_id and t.week_start == week_start), None)
        if not timetable:
            raise HTTPException(status_code=404, detail="Timetable not found")
        
        return timetable
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

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

@app.get("/timetables/{user_id}/{week_start}", response_model=Timetable)
async def get_weekly_timetable(user_id: int, week_start: date, current_user: UserInDB = Depends(get_current_user)):
    if current_user.role == "student" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Students can only view their own timetable")
    
    timetable = next((t for t in timetables_db if t.user_id == user_id and t.week_start == week_start), None)
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    
    return timetable

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
