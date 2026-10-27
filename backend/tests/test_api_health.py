"""
tests/test_api_health.py

Tests for the /api/health endpoint.
"""

import pytest


def test_health_returns_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "timestamp" in data
