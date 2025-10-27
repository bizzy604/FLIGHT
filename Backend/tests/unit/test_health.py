"""Basic health check tests."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns correct information."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "REA Flight Portal"
    assert data["version"] == "1.0.0"
    assert data["status"] == "running"


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_readiness_check():
    """Test readiness endpoint."""
    response = client.get("/health/ready")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


def test_liveness_check():
    """Test liveness endpoint."""
    response = client.get("/health/live")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
