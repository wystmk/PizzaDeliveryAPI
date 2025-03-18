import pytest
from fastapi.testclient import TestClient
from main import app  # Import the FastAPI app


client = TestClient(app)  # ✅ Create a synchronous test client

def test_register_user():
    """Test user registration"""
    response = client.post("/auth/signup", json={  # ✅ Change "/auth/register" -> "/auth/signup"
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "is_active": True,
        "is_staff": False
    })
    assert response.status_code == 201, response.text  # ✅ Expect HTTP 201 Created
    assert response.json()["username"] == "testuser"

def test_login_user():
    """Test user login and JWT retrieval"""
    response = client.post("/auth/login", json={  # ✅ Change `data=` to `json=`
        "username": "testuser",
        "password": "password123"
    })
    assert response.status_code == 200, response.text  # ✅ Expect HTTP 200 OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"