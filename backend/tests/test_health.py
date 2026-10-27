"""
Test suite for the health endpoint.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "AI Payment Reconciliation Agent"


def test_health_has_timestamp():
    response = client.get("/api/health")
    data = response.json()
    assert "timestamp" in data
    assert data["timestamp"] is not None
