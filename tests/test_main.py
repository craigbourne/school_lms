import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from main import app, create_access_token, get_password_hash # type: ignore
from auth import verify_password, decode_access_token # type: ignore
from models import form_body # type: ignore
import pytest

client = TestClient(app)

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to School LMS" in response.text

def test_user_registration_success():
    form_data = {
        "username": "testuser",
        "password": "testpassword",
        "email": "test@example.com",
        "role": "student",
        "year_group": "9"
    }
    response = client.post("/register", data=form_data)
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")
    assert response.status_code == 303  # Redirect status code
    assert response.headers["location"] == "/"  # Redirects to home page

def test_user_login_success():
    # Register a user
    client.post("/register", data={
        "username": "loginuser",
        "password": "loginpass",
        "email": "login@example.com",
        "role": "student",
        "year_group": "9"
    })

    # Try to login
    login_data = {
        "username": "loginuser",
        "password": "loginpass"
    }
    response = client.post("/login", data=login_data)
    assert response.status_code == 303  # Redirect status code
    assert response.headers["location"] == "/dashboard"  # Redirects to dashboard
    assert "access_token" in response.cookies


def test_protected_route_unauthorised():
    response = client.get("/protected")
    assert response.status_code == 401  # Unauthorised

def test_protected_route_authorised():
    # Register and login
    client.post("/register", data={
        "username": "protecteduser",
        "password": "protectedpass",
        "email": "protected@example.com",
        "role": "student",
        "year_group": "9"
    })
    login_response = client.post("/login", data={
        "username": "protecteduser",
        "password": "protectedpass"
    })

    # Get access token from the login response
    access_token = login_response.cookies.get("access_token")

    # Access the protected route
    response = client.get("/protected", cookies={"access_token": access_token})
    assert response.status_code == 200
    assert "This is a protected route" in response.json()["message"]

def test_create_lesson():
    # Register and login as a teacher
    client.post("/register", data={
        "username": "teacheruser",
        "password": "teacherpass",
        "email": "teacher@example.com",
        "role": "teacher"
    })
    login_response = client.post("/login", data={
        "username": "teacheruser",
        "password": "teacherpass"
    })
    access_token = login_response.cookies.get("access_token")

    # Create a lesson
    lesson_data = {
        "subject": "Math",
        "teacher": "teacheruser",
        "classroom": "Room 101",
        "day_of_week": "Monday",
        "start_time": "09:00",
        "end_time": "10:00",
        "year_group": 9
    }
    response = client.post("/lessons/", json=lesson_data, cookies={"access_token": access_token})
    assert response.status_code == 200
    assert response.json()["subject"] == "Math"

def test_view_timetable():
    # Register and login as a student
    client.post("/register", data={
        "username": "studentuser",
        "password": "studentpass",
        "email": "student@example.com",
        "role": "student",
        "year_group": "9"
    })
    login_response = client.post("/login", data={
        "username": "studentuser",
        "password": "studentpass"
    })
    access_token = login_response.cookies.get("access_token")

    # View timetable
    response = client.get("/timetable/", cookies={"access_token": access_token})
    assert response.status_code == 200
    assert "Weekly Timetable" in response.text
    assert "<table>" in response.text  # Check if timetable table is present
    assert "<th>Monday</th>" in response.text  # Check if days of the week are present
    assert "<td>09:00</td>" in response.text  # Check if time slots are present

def test_admin_login_success():
    # Register and login as an admin
    client.post("/register", data={
        "username": "adminuser",
        "password": "adminpass",
        "email": "admin@example.com",
        "role": "admin"
    })
    response = client.post("/login", data={
        "username": "adminuser",
        "password": "adminpass"
    })
    return response.cookies.get("access_token")

def test_teacher_login_success():
    client.post("/register", data={
        "username": "teacheruser",
        "password": "teacherpass",
        "email": "teacher@example.com",
        "role": "teacher"
    })
    response = client.post("/login", data={
        "username": "teacheruser",
        "password": "teacherpass"
    })
    return response.cookies.get("access_token")

def test_student_login_success():
    # Register and login as a student
    client.post("/register", data={
        "username": "studentuser",
        "password": "studentpass",
        "email": "student@example.com",
        "role": "student",
        "year_group": "9"
    })
    response = client.post("/login", data={
        "username": "studentuser",
        "password": "studentpass"
    })
    return response.cookies.get("access_token")

def test_register_duplicate_username():
    # Register a user
    client.post("/register", data={
        "username": "duplicateuser",
        "password": "testpass",
        "email": "duplicate@example.com",
        "role": "student",
        "year_group": "9"
    })
    
    # Try to register again with the same username
    response = client.post("/register", data={
        "username": "duplicateuser",
        "password": "anotherpass",
        "email": "another@example.com",
        "role": "student",
        "year_group": "9"
    })
    assert response.status_code == 200  # It should return to the registration page
    assert "Username already registered" in response.text

def test_invalid_login():
    response = client.post("/login", data={
        "username": "nonexistentuser",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert "Incorrect username or password" in response.text

def get_student_token():
    # Register and login as a student
    client.post("/register", data={
        "username": "logoutstudent",
        "password": "studentpass",
        "email": "logout@example.com",
        "role": "student",
        "year_group": "9"
    })
    response = client.post("/login", data={
        "username": "logoutstudent",
        "password": "studentpass"
    })
    return response.cookies.get("access_token")

def test_logout():
    student_token = get_student_token()
    response = client.get("/logout", cookies={"access_token": student_token})
    assert response.status_code == 200

    # Check if the access_token cookie is removed or expired
    access_token_cookie = next((cookie for cookie in response.cookies if cookie.key == "access_token"), None)
    assert access_token_cookie is None or access_token_cookie.value == ""

def test_view_lessons_as_student():
    student_token = get_student_token()
    response = client.get("/lessons/", cookies={"access_token": student_token})
    assert response.status_code == 200
    assert "Lesson List" in response.text

def test_add_lesson_as_teacher():
    teacher_token = test_teacher_login_success()
    response = client.post("/lessons/add/", data={
        "subject": "Physics",
        "teacher": "teacheruser",
        "classroom": "Lab 1",
        "day_of_week": "Tuesday",
        "start_time": "10:00",
        "year_group": "10"
    }, cookies={"access_token": teacher_token})
    assert response.status_code == 303
    assert response.headers["location"] == "/lessons/"

def test_delete_lesson_as_admin():
    admin_token = test_admin_login_success()
    # First, add a lesson
    client.post("/lessons/add/", data={
        "subject": "Biology",
        "teacher": "adminuser",
        "classroom": "Lab 4",
        "day_of_week": "Friday",
        "start_time": "14:00",
        "year_group": "10"
    }, cookies={"access_token": admin_token})

    # Now delete the lesson (assuming the lesson ID is 2)
    response = client.post("/lessons/2/delete", cookies={"access_token": admin_token})
    assert response.status_code == 303
    assert response.headers["location"] == "/lessons/"

def test_view_admin_timetables():
    admin_token = test_admin_login_success()
    response = client.get("/admin/timetables", cookies={"access_token": admin_token})
    assert response.status_code == 200
    assert "Admin Timetable View" in response.text

def test_student_cannot_access_admin_timetables():
    student_token = test_student_login_success()
    response = client.get("/admin/timetables", cookies={"access_token": student_token})
    assert response.status_code == 403

def test_create_timetable_as_admin():
    admin_token = test_admin_login_success()
    response = client.post("/timetables/", json={
        "user_id": 1,
        "week_start": "2023-01-01",
        "week_end": "2023-01-07"
    }, cookies={"access_token": admin_token})
    assert response.status_code == 200
    assert "id" in response.json()

def test_get_weekly_timetable():
    student_token = test_student_login_success()
    # Assuming the student's user_id is 1 and looking at the current week
    from datetime import date, timedelta
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    response = client.get(f"/timetables/11/{week_start}", cookies={"access_token": student_token})
    assert response.status_code == 200
    assert "lessons" in response.json()

def test_token_creation_and_validation():
    token = create_access_token(data={"sub": "testuser"})
    assert token is not None
    decoded_username = decode_access_token(token)
    assert decoded_username == "testuser"

def test_password_hashing():
    password = "testpassword"
    hashed_password = get_password_hash(password)
    assert verify_password(password, hashed_password)
    assert not verify_password("wrongpassword", hashed_password)
