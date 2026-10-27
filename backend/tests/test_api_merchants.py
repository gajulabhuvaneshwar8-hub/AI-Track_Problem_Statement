"""
tests/test_api_merchants.py

Tests for merchant CRUD endpoints.
"""

import pytest


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def test_create_merchant_success(client, auth_headers):
    resp = client.post(
        "/api/merchants",
        json={"name": "Acme Corp", "email": "billing@acme.com", "business_name": "Acme Corporation"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Acme Corp"
    assert data["email"] == "billing@acme.com"
    assert "id" in data
    assert "created_at" in data


def test_create_merchant_duplicate_email(client, auth_headers):
    payload = {"name": "Dup Merchant", "email": "dup@merchant.com"}
    client.post("/api/merchants", json=payload, headers=auth_headers)
    resp = client.post("/api/merchants", json=payload, headers=auth_headers)
    assert resp.status_code == 400


def test_create_merchant_requires_auth(client):
    resp = client.post(
        "/api/merchants",
        json={"name": "Anon Corp", "email": "anon@corp.com"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Get single
# ---------------------------------------------------------------------------

def test_get_merchant_success(client, auth_headers):
    create_resp = client.post(
        "/api/merchants",
        json={"name": "Get Corp", "email": "get@corp.com"},
        headers=auth_headers,
    )
    merchant_id = create_resp.json()["id"]
    resp = client.get(f"/api/merchants/{merchant_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == merchant_id


def test_get_merchant_not_found(client, auth_headers):
    resp = client.get(
        "/api/merchants/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

def test_list_merchants(client, auth_headers):
    client.post("/api/merchants", json={"name": "M1", "email": "m1@test.com"}, headers=auth_headers)
    client.post("/api/merchants", json={"name": "M2", "email": "m2@test.com"}, headers=auth_headers)
    resp = client.get("/api/merchants", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 2


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

def test_update_merchant(client, auth_headers):
    create_resp = client.post(
        "/api/merchants",
        json={"name": "Old Name", "email": "update@merchant.com"},
        headers=auth_headers,
    )
    merchant_id = create_resp.json()["id"]
    resp = client.put(
        f"/api/merchants/{merchant_id}",
        json={"name": "New Name"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def test_delete_merchant(client, auth_headers):
    create_resp = client.post(
        "/api/merchants",
        json={"name": "Delete Me", "email": "delete@merchant.com"},
        headers=auth_headers,
    )
    merchant_id = create_resp.json()["id"]
    resp = client.delete(f"/api/merchants/{merchant_id}", headers=auth_headers)
    assert resp.status_code == 204
    # Verify it's gone
    get_resp = client.get(f"/api/merchants/{merchant_id}", headers=auth_headers)
    assert get_resp.status_code == 404
