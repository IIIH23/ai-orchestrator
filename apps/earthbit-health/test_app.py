"""Tests for earthbit-health service."""
import pytest
from app import app


def test_health():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "earthbit-health"


def test_index():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
