# tests/test_security.py

import pytest
from fastapi.testclient import TestClient

class TestSecurityFeatures:
    """Test security implementations."""

    def test_security_headers(self, client: TestClient):
        """Test security headers are present."""
        response = client.get("/")

        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_rate_limiting(self, client: TestClient):
        """Test rate limiting works."""
        # Make many requests
        for i in range(65):  # Exceed minute limit
            response = client.get("/api/v1/health")

            if i < 60:
                assert response.status_code == 200
            else:
                assert response.status_code == 429
                assert "X-RateLimit-Reset" in response.headers

    def test_sql_injection_prevention(self, client: TestClient, auth_headers):
        """Test SQL injection is prevented."""
        malicious_input = "'; DROP TABLE users; --"

        response = client.get(
            f"/api/v1/users?search={malicious_input}",
            headers=auth_headers
        )

        # Should handle safely
        assert response.status_code in [200, 404]

    def test_xss_prevention(self, client: TestClient, auth_headers):
        """Test XSS prevention in inputs."""
        malicious_script = "<script>alert('XSS')</script>"

        response = client.post(
            "/api/v1/academic/programs",
            json={"name": malicious_script},
            headers=auth_headers
        )

        # Should sanitize the input
        if response.status_code == 201:
            assert "<script>" not in response.json()["data"]["name"]
