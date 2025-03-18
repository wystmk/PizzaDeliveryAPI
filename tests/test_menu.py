import pytest
from fastapi.testclient import TestClient
from main import app  # Import the FastAPI app

client = TestClient(app)  # ✅ Use TestClient for testing

def test_get_menu():
    """Test retrieving the pizza menu"""
    response = client.get("/menu")
    
    assert response.status_code == 200
    assert "menu" in response.json()
    assert isinstance(response.json()["menu"], list)
    assert len(response.json()["menu"]) > 0