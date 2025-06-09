"""
End-to-end tests for authentication flow.
"""

import pytest
from fastapi import status


class TestAuthenticationFlow:
    """Test complete authentication flows."""

    def test_login_success(self, client, test_user_admin):
        """Test successful login flow."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin@test.com",  # OAuth2 uses username field
                "password": "Admin123!",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client, test_user_admin):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "WrongPassword"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Incorrect email or password"

    def test_refresh_token_flow(self, client, test_user_admin):
        """Test token refresh flow."""
        # First login
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "Admin123!"},
        )

        tokens = login_response.json()["data"]

        # Use refresh token
        refresh_response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )

        assert refresh_response.status_code == status.HTTP_200_OK
        new_tokens = refresh_response.json()["data"]
        assert "access_token" in new_tokens
        assert new_tokens["access_token"] != tokens["access_token"]

    def test_protected_endpoint_with_token(self, client, test_user_admin, auth_headers):
        """Test accessing protected endpoint with valid token."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["email"] == "admin@test.com"
        assert data["role"]["name"] == "Administrator"

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Not authenticated"

    def test_change_password_flow(self, client, test_user_admin, auth_headers):
        """Test password change flow."""
        response = client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "Admin123!", "new_password": "NewAdmin123!"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["success"] is True

        # Try login with new password
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "NewAdmin123!"},
        )

        assert login_response.status_code == status.HTTP_200_OK
