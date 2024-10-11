import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from fastapi.testclient import TestClient
from main import app # type: ignore

client = TestClient(app)

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to School LMS" in response.text