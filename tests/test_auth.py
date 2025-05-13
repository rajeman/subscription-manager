import json
from app import db
from app.models import User
from werkzeug.security import generate_password_hash

def test_register_user_success(client, db):
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "password": "securepassword"
    }
    response = client.post('/api/v1/auth/register', json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == "User created"
    assert 'data' in data

def test_register_user_duplicate_email(client, db):
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "password": "securepassword"
    }
    client.post('/api/v1/auth/register', json=payload) 
    response = client.post('/api/v1/auth/register', json=payload) 
    assert response.status_code == 400
    data = response.get_json()
    assert "already exists" in data["message"]

def test_register_user_invalid_email(client, db):
    invalid_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "invalid_email",
        "password": "123456"
    }
    response = client.post('/api/v1/auth/register', json=invalid_data)
    assert response.status_code == 400
    assert "email" in response.get_json()

def test_login_with_wrong_password(client, db):
    user = User(
        first_name="Bob",
        last_name="Lee",
        email="bob@example.com",
        password=generate_password_hash("correctpass")
    )
    db.session.add(user)
    db.session.commit()

    payload = {
        "email": "bob@example.com",
        "password": "wrongpass"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert response.get_json()["message"] == "Invalid email or password"