"""
tests/test_api_auth.py

Tests for authentication endpoints:
  POST /api/auth/register
  POST /api/auth/login
  GET  /api/auth/me
"""

import pytest


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

def test_register_success(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "name": "Jane Doe",
            "email": "jane@exampledomain.com",
            "password": "StrongPass1",
            "role": "finance_user",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "jane@exampledomain.com"
    assert data["role"] == "finance_user"
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email(client):
    payload = {
        "name": "Alice",
        "email": "duplicate@exampledomain.com",
        "password": "StrongPass1",
    }
    resp1 = client.post("/api/auth/register", json=payload)
    assert resp1.status_code == 201
    resp2 = client.post("/api/auth/register", json=payload)
    assert resp2.status_code == 409
    assert resp2.json()["detail"] == "An account with this email already exists."


def test_register_password_too_short(client):
    resp = client.post(
        "/api/auth/register",
        json={"name": "Bob", "email": "bob@exampledomain.com", "password": "short"},
    )
    assert resp.status_code == 422  # Pydantic validation error


def test_register_invalid_email(client):
    resp = client.post(
        "/api/auth/register",
        json={"name": "Bob", "email": "not-an-email", "password": "StrongPass1"},
    )
    assert resp.status_code == 422


def test_register_missing_required_fields(client):
    # Missing email
    resp1 = client.post("/api/auth/register", json={"name": "No Email", "password": "StrongPass1"})
    assert resp1.status_code == 422

    # Missing password
    resp2 = client.post("/api/auth/register", json={"name": "No Pass", "email": "nopass@example.com"})
    assert resp2.status_code == 422

    # Missing name
    resp3 = client.post("/api/auth/register", json={"email": "noname@example.com", "password": "StrongPass1"})
    assert resp3.status_code == 422


def test_register_password_hashing(client, db_session):
    from app.core.security import verify_password
    from app.models.user import User

    email = "hashedcheck@exampledomain.com"
    plain = "MySecretPassword99"
    resp = client.post(
        "/api/auth/register",
        json={"name": "Hash Check", "email": email, "password": plain},
    )
    assert resp.status_code == 201
    user = db_session.query(User).filter(User.email == email).first()
    assert user is not None
    assert user.password_hash != plain
    assert user.password_hash.startswith("$2")  # bcrypt prefix
    assert verify_password(plain, user.password_hash)


def test_register_default_role(client):
    resp = client.post(
        "/api/auth/register",
        json={"name": "Default Role", "email": "defaultrole@exampledomain.com", "password": "StrongPass1"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "finance_user"


def test_register_database_rollback_on_failure(client, monkeypatch):
    from unittest.mock import MagicMock
    from app.services import user_service

    def fail_create_user(db, payload):
        raise RuntimeError("Simulated unexpected DB failure")

    monkeypatch.setattr(user_service, "create_user", fail_create_user)
    resp = client.post(
        "/api/auth/register",
        json={"name": "Fail Test", "email": "failtest@exampledomain.com", "password": "StrongPass1"},
    )
    assert resp.status_code == 500
    assert resp.json()["detail"] == "A server error occurred. Please try again later."


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def test_login_success(client):
    client.post(
        "/api/auth/register",
        json={"name": "Login User", "email": "loginuser@exampledomain.com", "password": "MyP@ss123"},
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": "loginuser@exampledomain.com", "password": "MyP@ss123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "loginuser@exampledomain.com"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]


def test_login_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={"name": "Pass User", "email": "passtest@exampledomain.com", "password": "CorrectP@ss1"},
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": "passtest@exampledomain.com", "password": "WrongPassword"},
    )
    assert resp.status_code == 401


def test_login_nonexistent_user(client):
    resp = client.post(
        "/api/auth/login",
        json={"email": "ghost@exampledomain.com", "password": "AnyPass123"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /me — protected endpoint
# ---------------------------------------------------------------------------

def test_me_with_valid_token(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@testexample.com"


def test_me_without_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_with_invalid_token(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401
