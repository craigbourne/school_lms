# Ensure absolute imports are used
from __future__ import absolute_import

# Standard library imports
import random
from datetime import date, datetime, time, timedelta
from typing import List, Optional

# FastAPI and related imports
from fastapi import (
    Depends,
    FastAPI,
    Form,
    HTTPException,
    Request,
    Response,
    status
  )
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Third-party imports for JWT handling and password hashing
from jose import jwt, JWTError
from passlib.context import CryptContext

# Local imports from auth and models modules
from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    create_access_token,
    get_user,
    SECRET_KEY,
    UserInDB
)
from models import (
    Lesson,
    LessonCreate,
    Timetable,
    TimetableCreate,
    RegisterModel
)

# Initialise FastAPI application
app = FastAPI()
# Set up Jinja2 HTML templates
templates = Jinja2Templates(directory="templates")
# Mount a static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
# Set up password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Set up OAuth2 password flow for token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialise empty databases
users_db = [] # Simulated database for users
lessons_db = [] # Simulated database for lessons
global_lessons_db = []  # Initialise global_lessons_db as an empty list
timetables_db: List[Timetable] = [] # Simulated database for timetable

login_attempts = {} # track login attempts

# Helper functions
# Verifies a plain password against a hashed password
def verify_password(plain_password, hashed_password):
    print(f"Verifying password: {plain_password}")
    print(f"Hashed password: {hashed_password}")
    result = pwd_context.verify(plain_password, hashed_password)
    print(f"Password verification result: {result}")
    return result

# Generates a hash for the given password
def get_password_hash(password):
    return pwd_context.hash(password)

# Authenticates a user based on username and password
def authenticate_user(username: str, password: str):
    print(f"Attempting to authenticate user: {username}")
    user = auth.get_user(username)
    if not user:
        print(f"User not found: {username}")
        return False
    print(f"User found: {user}")
    if not auth.verify_password(password, user.hashed_password):
        print(f"Password verification failed for user: {username}")
        return False
    print(f"Authentication successful for user: {username}")
    return user

# Retrieves the current user based on the JWT token in the request cookies
async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Not authenticated"
        )

    scheme, _, param = token.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Invalid authentication scheme"
        )

    try:
        payload = jwt.decode(param, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
                )
        user = get_user(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
                )
        return user
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
            ) from exc

# Checks if a new lesson conflicts with existing lessons for a user
def check_lesson_conflict(new_lesson, user_id):
    timetable = next((
        t for t in timetables_db if t.user_id == user_id),
        None
        )
    if timetable:
        for lesson in timetable.lessons:
            if (lesson.day_of_week == new_lesson.day_of_week and
                lesson.start_time == new_lesson.start_time and
                lesson.teacher == new_lesson.teacher):
                return True
    return False

# Mock data creation functions
# Creates test user accounts with predefined roles
def create_test_accounts():
    global users_db # pylint: disable=global-variable-not-assigned
    test_accounts = [
        {"username": "admin",
        "password": "adminpass",
        "role": "admin",
        "email": "admin@school.com"
        },
        {"username": "teacher1",
        "password": "teacherpass",
        "role": "teacher",
        "email": "teacher1@school.com"
        },
        {"username": "student1",
        "password": "studentpass",
        "role": "student",
        "year_group": 9,
        "email": "student1@school.com"
        }
    ]
    for account in test_accounts:
        if not any(user.username == account["username"] for user in users_db):
            hashed_password = get_password_hash(account["password"])
            new_user = UserInDB(
                id=len(users_db) + 1,
                username=account["username"],
                email=account["email"],
                hashed_password=hashed_password,
                role=account["role"],
                year_group=account.get("year_group")
            )
            users_db.append(new_user)
            print("Created test account: " +
            f"{account['username']} ({account['role']})")
    print(f"Current users in db: {users_db}")

# Creates mock teacher accounts with random subjects
def create_mock_teachers():
    subjects = [
        "Math",
        "English",
        "Science",
        "History",
        "Geography",
        "Art",
        "Music",
        "Physical Education"
        ]
    teachers = []
    for i in range(5):  # Create 5 teachers
        teacher_data = {
            "id": i + 1,
            "username": f"teacher{i+1}",
            "email": f"teacher{i+1}@school.com",
            "hashed_password": get_password_hash("password"),
            "role": "teacher",
            "subjects": random.sample(subjects, 2)
        }
        teacher = UserInDB(**teacher_data)
        teachers.append(teacher)
    return teachers

# Creates mock student accounts with random year groups
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

# Creates mock lessons for teachers and year groups
def create_mock_lessons():
    global global_lessons_db # pylint: disable=global-statement
    teachers = create_mock_teachers()
    subjects = [
        "Math",
        "English",
        "Science",
        "History",
        "Geography",
        "Art",
        "Music",
        "Physical Education"
        ]
    lesson_id = 1
    lesson_slots = {
    day: {
        hour: {year: None for year in range(7, 12)}
        for hour in range(9, 15)
        }
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    }

    global_lessons_db = []  # Reset global_lessons_db

    for teacher in teachers:
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            for hour in range(9, 15):
                if random.random() < 0.7:  # 70% chance of creating a lesson
                    subject = random.choice(subjects)
                    available_years = [
                        year for year,
                        lesson in lesson_slots[day][hour].items()
                        if lesson is None
                        ]
                    if not available_years:
                        continue
                    year_group = random.choice(available_years)
                    new_lesson = Lesson(
                        id=lesson_id,
                        subject=subject,
                        teacher=teacher.username,
                        classroom=f"Room {random.randint(101, 120)}",
                        day_of_week=day,
                        start_time=time(hour=hour),
                        end_time=time(hour=hour+1),
                        year_group=year_group
                    )
                    global_lessons_db.append(new_lesson)
                    lesson_slots[day][hour][year_group] = new_lesson
                    lesson_id += 1

                    # Print the newly created lesson
                    print("Created lesson: " +
                    f"{new_lesson.subject} on {new_lesson.day_of_week} at " +
                    f"{new_lesson.start_time} " + 
                    f"for Year {new_lesson.year_group} " +
                    f"in {new_lesson.classroom} with {new_lesson.teacher}")

    return global_lessons_db

# Creates mock timetables for users based on their roles
def create_mock_timetables():
    global global_lessons_db # pylint: disable=global-statement
    users = users_db
    timetables = []

    if global_lessons_db is None:
        global_lessons_db = []  # Initialise if it's None

    for user in users:
        user_lessons = []
        if user.role == "student":
            user_lessons = [
                lesson for lesson in global_lessons_db
                if lesson.year_group == user.year_group
                ]
        elif user.role == "teacher":
            user_lessons = [
                lesson for lesson in global_lessons_db
                if lesson.teacher == user.username
                ]
        else:  # admin sees all lessons
            user_lessons = global_lessons_db.copy()

        timetable = Timetable(
            id=len(timetables) + 1,
            user_id=user.id,
            week_start=date.today() - timedelta(days=date.today().weekday()),
            week_end=date.today() + timedelta(days=6),
            lessons=user_lessons
        )
        timetables.append(timetable)

    return timetables

# Initialise mock data
# Create predefined test accounts (admin, teacher, student)
create_test_accounts()

# Add additional mock teachers and students to the users database
users_db.extend(create_mock_teachers() + create_mock_students())

# Generate mock lessons and store them in the global lessons database
global_lessons_db = create_mock_lessons()

# Create mock timetables
timetables_db = create_mock_timetables()

# Share the users_db with the auth module
import auth
auth.users_db = users_db


# Route definitions
# Auth routes
# Renders the home page
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Handles user registration
@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    year_group: Optional[int] = Form(None)
):
    register_data = RegisterModel(
        username=username,
        password=password,
        email=email,
        role=role,
        year_group=year_group
    )
    print(f"Received registration data: {register_data}")

    if register_data.role not in ["admin", "teacher", "student"]:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Invalid role"}
        )

    if any(user.username == register_data.username for user in users_db):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username already registered"}
        )

    if register_data.role == "student" and not register_data.year_group:
        return templates.TemplateResponse(
            "register.html",
            {"request": request,
            "error": "Year group is required for students"
            }
        )

    hashed_password = get_password_hash(register_data.password)
    new_user = UserInDB(
        id=len(users_db) + 1,
        username=register_data.username,
        email=register_data.email,
        hashed_password=hashed_password,
        role=register_data.role,
        year_group=(
        register_data.year_group
        if register_data.role == "student"
        else None
        )
    )
    users_db.append(new_user)

    # Create a timetable for the new user
    new_timetable = Timetable(
        id=len(timetables_db) + 1,
        user_id=new_user.id,
        week_start=date.today() - timedelta(days=date.today().weekday()),
        week_end=date.today() + timedelta(days=6),
        lessons=[]
    )
    timetables_db.append(new_timetable)

    return RedirectResponse(url="/", status_code=303)

# Renders the registration form page
@app.get("/register")
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Handles user login and sets JWT token in cookies
@app.post("/login")
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends()
    ):
    print(f"Login route called for user: {form_data.username}")
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

# Handles user logout by deleting the access token cookie
@app.get("/logout")
async def logout(request: Request): # pylint: disable=unused-argument
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response

# Generates and returns a JWT access token for authenticated users
@app.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
    ):
    print(f"Login attempt for user: {form_data.username}")
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        print(f"Authentication failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print(f"Authentication successful for user: {form_data.username}")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Dashboard and user info routes
# Renders the user dashboard
@app.get("/dashboard")
async def dashboard(
    request: Request,
    current_user: UserInDB = Depends(get_current_user)
    ):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": current_user}
        )

# Returns information about the current authenticated user
@app.get("/users/me")
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return current_user


# Lesson routes
# Lists lessons based on the user's role
@app.get("/lessons/")
async def list_lessons(
    request: Request,
    current_user: UserInDB = Depends(get_current_user)
    ):
    if current_user.role == 'admin':
        visible_lessons = global_lessons_db
    elif current_user.role == 'teacher':
        visible_lessons = [
            lesson for lesson in global_lessons_db
            if lesson.teacher == current_user.username
            ]
    else:
        visible_lessons = [
            lesson for lesson in global_lessons_db
            if lesson.year_group == current_user.year_group
            ]

    # Sort lessons by day of week and start time
    day_order = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4
        }
    sorted_lessons = sorted(
        visible_lessons,
        key=lambda x: (day_order[x.day_of_week], x.start_time)
        )

    return templates.TemplateResponse(
        "lesson_list.html",
        {"request": request,
        "lessons": sorted_lessons,
        "current_user": current_user
        }
      )

# Retrieves a specific lesson by ID
@app.get("/lessons/{lesson_id}", response_model=Lesson)
async def get_lesson(
    lesson_id: int,
    # current_user: UserInDB = Depends(get_current_user)
    ):
    lesson = next((
        lesson for lesson in global_lessons_db
        if lesson.id == lesson_id),
        None
        )
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson

# Creates a new lesson
@app.post("/lessons/", response_model=Lesson)
async def create_lesson(
    lesson: LessonCreate,
    current_user: UserInDB = Depends(get_current_user)
    ):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators and teachers can create lessons"
            )

    if (current_user.role == "teacher"and
        lesson.teacher != current_user.username
        ):
        raise HTTPException(
            status_code=403,
            detail="Teachers can only create lessons for themselves"
            )

    if check_lesson_conflict(lesson, current_user.id):
        raise HTTPException(
            status_code=400,
            detail="You already have a lesson scheduled at this time"
            )

    new_lesson = Lesson(id=len(global_lessons_db) + 1, **lesson.dict())
    global_lessons_db.append(new_lesson)

    # Update timetables
    for timetable in timetables_db:
        if (current_user.role == "admin" or
            (current_user.role == "teacher" and
            new_lesson.teacher == current_user.username) or
            new_lesson.year_group == current_user.year_group
            ):
            timetable.lessons.append(new_lesson)

    return new_lesson

# Updates an existing lesson
@app.put("/lessons/{lesson_id}", response_model=Lesson)
async def update_lesson(
    lesson_id: int,
    updated_lesson: LessonCreate,
    current_user: UserInDB = Depends(get_current_user)
    ):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators and teachers can update lessons"
            )

    lesson_index = next(
        (i for i, lesson in enumerate(lessons_db)
        if lesson.id == lesson_id),
        None
        )
    if lesson_index is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    if (current_user.role == "teacher" and
    lessons_db[lesson_index].teacher != current_user.username):
        raise HTTPException(status_code=403,
                            detail="Teachers can only update their own lessons"
                            )

    if check_lesson_conflict(updated_lesson, current_user.id):
        raise HTTPException(
            status_code=400,
            detail="This lesson conflicts with an existing lesson"
            )

    updated_lesson_dict = updated_lesson.dict()
    updated_lesson_dict['id'] = lesson_id
    lessons_db[lesson_index] = Lesson(**updated_lesson_dict)

    # Update timetables
    for timetable in timetables_db:
        for i, lesson in enumerate(timetable.lessons):
            if lesson.id == lesson_id:
                timetable.lessons[i] = lessons_db[lesson_index]

    return lessons_db[lesson_index]

# Deletes a lesson
@app.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: int,
    current_user: UserInDB = Depends(get_current_user)
    ):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can delete lessons"
            )

    for i, lesson in enumerate(lessons_db):
        if lesson.id == lesson_id:
            lessons_db.pop(i)
            # Remove lesson from timetables
            for timetable in timetables_db:
                timetable.lessons = [
                    l for l in timetable.lessons
                    if l.id != lesson_id
                    ]
            return
    raise HTTPException(status_code=404, detail="Lesson not found")

# Renders the form for adding a new lesson
@app.get("/lessons/add/")
async def lesson_add_form(
    request: Request,
    current_user: UserInDB = Depends(get_current_user)
    ):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators and teachers can add lessons"
            )
    return templates.TemplateResponse("lesson_add.html", {"request": request})

# Handles the submission of a new lesson
@app.post("/lessons/add/")
async def lesson_add(
    request: Request, # pylint: disable=unused-argument
    subject: str = Form(...),
    teacher: str = Form(...),
    classroom: str = Form(...),
    day_of_week: str = Form(...),
    start_time: str = Form(...),
    year_group: int = Form(...),
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators and teachers can add lessons"
        )

    new_lesson = LessonCreate(
        subject=subject,
        teacher=teacher,
        classroom=classroom,
        day_of_week=day_of_week,
        start_time=datetime.strptime(start_time, "%H:%M").time(),
        end_time=(
            datetime.strptime(start_time, "%H:%M") + timedelta(hours=1)
            ).time(),
        year_group=year_group
    )

    await create_lesson(new_lesson, current_user)
    return RedirectResponse(url="/lessons/", status_code=303)

# Renders the form for editing an existing lesson
@app.get("/lessons/{lesson_id}/edit")
async def lesson_edit_form(
    lesson_id: int,
    request: Request,
    current_user: UserInDB = Depends(get_current_user)
    ):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators and teachers can edit lessons"
            )

    lesson = next(
        (lesson for lesson in global_lessons_db if lesson.id == lesson_id),
        None
    )
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return templates.TemplateResponse(
        "lesson_edit.html",
        {"request": request, "lesson": lesson}
        )

# Handles the submission of an edited lesson
@app.post("/lessons/{lesson_id}/edit")
async def lesson_edit(
    lesson_id: int,
    request: Request,  #pylint: disable=unused-argument
    subject: str = Form(...),
    teacher: str = Form(...),
    classroom: str = Form(...),
    day_of_week: str = Form(...),
    start_time: str = Form(...),
    year_group: int = Form(...),
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators and teachers can edit lessons"
        )

    lesson = next(
        (lesson for lesson in global_lessons_db if lesson.id == lesson_id),
        None
    )
    if lesson is None:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found"
            )

    if (current_user.role == "teacher" and
        lesson.teacher != current_user.username):
        raise HTTPException(
            status_code=403,
            detail="Teachers can only update their own lessons"
        )

    # Update the lesson
    lesson.subject = subject
    lesson.teacher = teacher
    lesson.classroom = classroom
    lesson.day_of_week = day_of_week
    lesson.start_time = datetime.strptime(
        start_time, "%H:%M"
        ).time()
    lesson.end_time = (datetime.strptime(
        start_time, "%H:%M") + timedelta(hours=1)
        ).time()
    lesson.year_group = year_group

    # Update the lesson in all timetables
    for timetable in timetables_db:
        for i, timetable_lesson in enumerate(timetable.lessons):
            if timetable_lesson.id == lesson_id:
                timetable.lessons[i] = lesson

    return RedirectResponse(url="/lessons/", status_code=303)

# Handles the deletion of a lesson
@app.post("/lessons/{lesson_id}/delete")
async def lesson_delete(
      lesson_id: int,
      current_user: UserInDB = Depends(get_current_user)
    ):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can delete lessons"
            )

    lesson = next(
        (lesson for lesson in global_lessons_db if lesson.id == lesson_id),
        None
    )
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    global_lessons_db.remove(lesson)

    # Remove lesson from timetables
    for timetable in timetables_db:
        timetable.lessons = [l for l in timetable.lessons if l.id != lesson_id]

    return RedirectResponse(url="/lessons/", status_code=303)


# Timetable routes
# Renders the timetable view for the current user
@app.get("/timetable/")
async def view_timetable(
    request: Request,
    current_user: UserInDB = Depends(get_current_user)
    ):
    timetable = next((
        t for t in timetables_db
        if t.user_id == current_user.id),
        None
        )

    if not timetable:
        return templates.TemplateResponse("timetable_view.html", {
            "request": request,
            "current_user": current_user,
            "timetable": None
        })

    # Sort lessons by day of week and start time
    day_order = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4
        }
    sorted_lessons = sorted(
        timetable.lessons,
        key=lambda x: (day_order[x.day_of_week], x.start_time))

    # Group lessons by day
    lessons_by_day = {
        day: []
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        }
    for lesson in sorted_lessons:
        lessons_by_day[lesson.day_of_week].append(lesson)

    return templates.TemplateResponse("timetable_view.html", {
        "request": request,
        "current_user": current_user,
        "timetable": timetable,
        "lessons_by_day": lessons_by_day
    })

# Retrieves a weekly timetable for a specific user and week
@app.get("/timetables/{user_id}/{week_start}", response_model=Timetable)
async def get_weekly_timetable(
    user_id: int,
    week_start: date,
    current_user: UserInDB = Depends(get_current_user)
    ):
    print(
        f"Searching for timetable: user_id={user_id}, "
        f"week_start={week_start}"
    )
    print(f"Current timetables in db: {timetables_db}")

    if current_user.role == "student" and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Students can only view their own timetable"
            )

    timetable = next((
        t for t in timetables_db
        if t.user_id == user_id and t.week_start == week_start),
        None
        )
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")

    return timetable

# Retrieves a timetable for a specific user
@app.get("/timetables/{user_id}", response_model=Timetable)
async def get_timetable(
    user_id: int,
    week_start: date,
    current_user: UserInDB = Depends(get_current_user)):
    try:
        if (current_user.id != user_id and
            current_user.role not in ["admin", "teacher"]):
            raise HTTPException(
                status_code=403,
                detail="You can only view your own timetable"
            )

        timetable = next((
            t for t in timetables_db
            if t.user_id == user_id and t.week_start == week_start),
            None
            )
        if not timetable:
            raise HTTPException(status_code=404, detail="Timetable not found")

        return timetable
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format"
            ) from exc
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
            ) from e

# Creates a new timetable
@app.post("/timetables/", response_model=Timetable)
async def create_timetable(
    timetable: TimetableCreate,
    current_user: UserInDB = Depends(get_current_user)
    ):
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators and teachers can create timetables"
            )

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


# Admin routes
# Renders the admin view of all timetables with optional filtering
@app.get("/admin/timetables")
async def admin_timetables(
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
    teacher: Optional[str] = None,
    year_group: Optional[int] = None
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can access this page"
            )

    filtered_timetables = timetables_db

    if teacher:
        filtered_timetables = [
            t for t in filtered_timetables
            if any(lesson.teacher == teacher for lesson in t.lessons)
            ]

    if year_group:
        filtered_timetables = [
            t for t in filtered_timetables
            if any(lesson.year_group == year_group for lesson in t.lessons)
            ]

    return templates.TemplateResponse(
        "admin_timetables.html",
        {
            "request": request,
            "timetables": filtered_timetables,
            "teachers": list(set(
                lesson.teacher
                for timetable in timetables_db
                for lesson in timetable.lessons
                )),
            "year_groups": list(range(7, 12))
        }
    )

# A sample protected route that requires authentication
@app.get("/protected")
async def protected_route(current_user: UserInDB = Depends(get_current_user)):
    return {"message":
            f"Hello, {current_user.username}! This is a protected route."
            }

# Main execution block
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
