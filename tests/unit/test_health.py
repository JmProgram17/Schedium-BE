"""
Unit tests for health endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "environment" in data


def test_health_endpoint(client: TestClient):
    """Test health endpoint returns system status."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "app" in data
    assert data["status"] in ["healthy", "unhealthy"]


def test_api_health_endpoint(client: TestClient):
    """Test API v1 health endpoint."""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["status"] in ["healthy", "degraded"]


def test_api_ready_endpoint(client: TestClient):
    """Test API v1 readiness endpoint."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "ready" in data["data"]


def test_api_live_endpoint(client: TestClient):
    """Test API v1 liveness endpoint."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["alive"] is True
