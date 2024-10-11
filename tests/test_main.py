import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from main import app # type: ignore

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
