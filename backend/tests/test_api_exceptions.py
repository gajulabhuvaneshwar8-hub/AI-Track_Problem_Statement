"""
tests/test_api_exceptions.py

Tests for reconciliation exception management endpoints.
"""

import pytest


EXC_PAYLOAD = {
    "severity": "high",
    "category": "amount_mismatch",
    "title": "Gateway amount does not match bank",
    "description": "Expected 1000.00 but bank reports 999.50",
    "status": "open",
}


def test_create_exception_success(client, auth_headers):
    resp = client.post("/api/exceptions", json=EXC_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["severity"] == "high"
    assert data["status"] == "open"
    assert "id" in data


def test_create_exception_requires_auth(client):
    resp = client.post("/api/exceptions", json=EXC_PAYLOAD)
    assert resp.status_code == 401


def test_list_exceptions(client, auth_headers):
    client.post("/api/exceptions", json=EXC_PAYLOAD, headers=auth_headers)
    resp = client.get("/api/exceptions", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1


def test_filter_exceptions_by_severity(client, auth_headers):
    client.post(
        "/api/exceptions",
        json={**EXC_PAYLOAD, "severity": "critical", "title": "Critical issue"},
        headers=auth_headers,
    )
    resp = client.get("/api/exceptions?severity=critical", headers=auth_headers)
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["severity"] == "critical"


def test_filter_exceptions_by_status(client, auth_headers):
    client.post(
        "/api/exceptions",
        json={**EXC_PAYLOAD, "status": "open", "title": "Open exception"},
        headers=auth_headers,
    )
    resp = client.get("/api/exceptions?status=open", headers=auth_headers)
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["status"] == "open"


def test_get_exception_by_id(client, auth_headers):
    create = client.post("/api/exceptions", json=EXC_PAYLOAD, headers=auth_headers)
    exc_id = create.json()["id"]
    resp = client.get(f"/api/exceptions/{exc_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == exc_id


def test_get_exception_not_found(client, auth_headers):
    resp = client.get(
        "/api/exceptions/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_update_exception_status(client, auth_headers):
    create = client.post("/api/exceptions", json=EXC_PAYLOAD, headers=auth_headers)
    exc_id = create.json()["id"]

    resp = client.put(
        f"/api/exceptions/{exc_id}",
        json={"status": "investigating"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "investigating"


def test_resolve_exception_sets_resolved_at(client, auth_headers):
    create = client.post("/api/exceptions", json=EXC_PAYLOAD, headers=auth_headers)
    exc_id = create.json()["id"]

    resp = client.put(
        f"/api/exceptions/{exc_id}",
        json={"status": "resolved"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "resolved"
    assert data["resolved_at"] is not None
