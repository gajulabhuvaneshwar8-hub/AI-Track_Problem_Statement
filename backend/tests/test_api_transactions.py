"""
tests/test_api_transactions.py

Tests for transaction CRUD and filtering endpoints.
"""

import pytest


TXN_PAYLOAD = {
    "transaction_reference": "TXN-TEST-001",
    "amount": "250.50",
    "currency": "USD",
    "transaction_date": "2024-06-01T12:00:00Z",
    "payment_method": "card",
    "gateway": "Stripe",
    "status": "success",
    "source": "gateway",
}


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def test_create_transaction_success(client, auth_headers):
    resp = client.post("/api/transactions", json=TXN_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["transaction_reference"] == "TXN-TEST-001"
    assert data["amount"] == "250.5000"  # Numeric(18,4) returns 4dp
    assert "id" in data


def test_create_transaction_duplicate_reference(client, auth_headers):
    client.post("/api/transactions", json=TXN_PAYLOAD, headers=auth_headers)
    resp = client.post(
        "/api/transactions",
        json={**TXN_PAYLOAD, "transaction_reference": "TXN-TEST-001"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_create_transaction_negative_amount(client, auth_headers):
    resp = client.post(
        "/api/transactions",
        json={**TXN_PAYLOAD, "transaction_reference": "TXN-NEG-001", "amount": "-10"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_transaction_requires_auth(client):
    resp = client.post("/api/transactions", json=TXN_PAYLOAD)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Get single
# ---------------------------------------------------------------------------

def test_get_transaction(client, auth_headers):
    create = client.post(
        "/api/transactions",
        json={**TXN_PAYLOAD, "transaction_reference": "TXN-GET-001"},
        headers=auth_headers,
    )
    txn_id = create.json()["id"]
    resp = client.get(f"/api/transactions/{txn_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == txn_id


def test_get_transaction_not_found(client, auth_headers):
    resp = client.get(
        "/api/transactions/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# List & filter
# ---------------------------------------------------------------------------

def test_list_transactions_paginated(client, auth_headers):
    for i in range(3):
        client.post(
            "/api/transactions",
            json={**TXN_PAYLOAD, "transaction_reference": f"TXN-LIST-{i:03d}"},
            headers=auth_headers,
        )
    resp = client.get("/api/transactions?page=1&page_size=10", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 10


def test_filter_transactions_by_status(client, auth_headers):
    client.post(
        "/api/transactions",
        json={**TXN_PAYLOAD, "transaction_reference": "TXN-FILT-001", "status": "success"},
        headers=auth_headers,
    )
    client.post(
        "/api/transactions",
        json={**TXN_PAYLOAD, "transaction_reference": "TXN-FILT-002", "status": "failed"},
        headers=auth_headers,
    )
    resp = client.get("/api/transactions?status=success", headers=auth_headers)
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["status"] == "success"


def test_filter_transactions_by_gateway(client, auth_headers):
    client.post(
        "/api/transactions",
        json={**TXN_PAYLOAD, "transaction_reference": "TXN-GW-001", "gateway": "PayPal"},
        headers=auth_headers,
    )
    resp = client.get("/api/transactions?gateway=PayPal", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(t["gateway"] == "PayPal" for t in items)


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

def test_update_transaction(client, auth_headers):
    create = client.post(
        "/api/transactions",
        json={**TXN_PAYLOAD, "transaction_reference": "TXN-UPD-001"},
        headers=auth_headers,
    )
    txn_id = create.json()["id"]
    resp = client.put(
        f"/api/transactions/{txn_id}",
        json={"status": "pending"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"
