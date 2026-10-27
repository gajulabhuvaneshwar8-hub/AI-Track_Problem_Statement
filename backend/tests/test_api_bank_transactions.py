"""
tests/test_api_bank_transactions.py

Tests for bank transaction CRUD endpoints.
"""

import pytest


BT_PAYLOAD = {
    "bank_reference": "BNK-TEST-001",
    "amount": "1000.00",
    "transaction_date": "2024-06-01T09:00:00Z",
    "description": "Payment for order ORD-001",
    "bank_name": "HSBC",
    "status": "posted",
}


def test_create_bank_transaction(client, auth_headers):
    resp = client.post("/api/bank-transactions", json=BT_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["bank_reference"] == "BNK-TEST-001"
    assert data["bank_name"] == "HSBC"
    assert "id" in data


def test_create_bank_transaction_duplicate_reference(client, auth_headers):
    client.post("/api/bank-transactions", json=BT_PAYLOAD, headers=auth_headers)
    resp = client.post("/api/bank-transactions", json=BT_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 400


def test_create_bank_transaction_requires_auth(client):
    resp = client.post("/api/bank-transactions", json=BT_PAYLOAD)
    assert resp.status_code == 401


def test_list_bank_transactions(client, auth_headers):
    for i in range(2):
        client.post(
            "/api/bank-transactions",
            json={**BT_PAYLOAD, "bank_reference": f"BNK-LIST-{i:03d}"},
            headers=auth_headers,
        )
    resp = client.get("/api/bank-transactions?page=1&page_size=10", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


def test_filter_bank_transactions_by_bank_name(client, auth_headers):
    client.post(
        "/api/bank-transactions",
        json={**BT_PAYLOAD, "bank_reference": "BNK-FILT-001", "bank_name": "BarclaysTest"},
        headers=auth_headers,
    )
    resp = client.get("/api/bank-transactions?bank_name=BarclaysTest", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all("BarclaysTest" in (item["bank_name"] or "") for item in items)


def test_get_bank_transaction(client, auth_headers):
    create = client.post(
        "/api/bank-transactions",
        json={**BT_PAYLOAD, "bank_reference": "BNK-GET-001"},
        headers=auth_headers,
    )
    bt_id = create.json()["id"]
    resp = client.get(f"/api/bank-transactions/{bt_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == bt_id


def test_get_bank_transaction_not_found(client, auth_headers):
    resp = client.get(
        "/api/bank-transactions/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert resp.status_code == 404
