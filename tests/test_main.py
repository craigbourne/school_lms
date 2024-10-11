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
    # First, register a user
    client.post("/register", data={
        "username": "loginuser",
        "password": "loginpass",
        "email": "login@example.com",
        "role": "student",
        "year_group": "9"
    })
    
    # Now, try to login
    login_data = {
        "username": "loginuser",
        "password": "loginpass"
    }
    response = client.post("/login", data=login_data)
    assert response.status_code == 303  # Redirect status code
    assert response.headers["location"] == "/dashboard"  # Redirects to dashboard
    assert "access_token" in response.cookies
