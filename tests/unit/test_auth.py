"""
Unit tests for authentication endpoints (app/routers/auth.py).

These tests exercise:
  POST /api/v1/auth/register
  POST /api/v1/auth/login
  POST /api/v1/auth/google
  POST /api/v1/auth/refresh
  GET  /api/v1/auth/me
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.schemas.auth import AuthResponse, UserResponse, TokenResponse


# ---------------------------------------------------------------------------
# POST /register – validation
# ---------------------------------------------------------------------------


class TestRegisterValidation:
    """Request-body validation for /register."""

    def test_missing_password_returns_422(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "a@b.com"},
        )
        assert resp.status_code == 422

    def test_missing_email_returns_422(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={"password": "StrongPass1"},
        )
        assert resp.status_code == 422

    def test_invalid_email_returns_422(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "StrongPass1"},
        )
        assert resp.status_code == 422

    def test_weak_password_no_uppercase_returns_422(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "a@b.com", "password": "alllower1"},
        )
        assert resp.status_code == 422

    def test_weak_password_no_digit_returns_422(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "a@b.com", "password": "NoDigitHere"},
        )
        assert resp.status_code == 422

    def test_short_password_returns_422(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "a@b.com", "password": "Sh0rt"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /register – happy path (mocked service)
# ---------------------------------------------------------------------------


class TestRegisterSuccess:
    """Successful registration through mocked AuthService."""

    @patch("app.services.auth_service.AuthService.register_user", new_callable=AsyncMock)
    def test_register_returns_201_with_tokens(self, mock_reg, client, test_user):
        mock_reg.return_value = AuthResponse(
            user=UserResponse(
                id=str(test_user.id),
                email="new@dowhat.com",
                email_verified=False,
                auth_provider="email",
                created_at=datetime(2025, 1, 1),
                last_login_at=None,
            ),
            access_token="fake-access",
            refresh_token="fake-refresh",
            token_type="bearer",
            expires_in=900,
        )
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "new@dowhat.com", "password": "GoodPass1"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "new@dowhat.com"


# ---------------------------------------------------------------------------
# POST /login – validation
# ---------------------------------------------------------------------------


class TestLoginValidation:
    """Request-body validation for /login."""

    def test_missing_email_returns_422(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"password": "whatever"},
        )
        assert resp.status_code == 422

    def test_missing_password_returns_422(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "a@b.com"},
        )
        assert resp.status_code == 422

    def test_invalid_email_returns_422(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "bad-email", "password": "x"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /google – validation
# ---------------------------------------------------------------------------


class TestGoogleAuthValidation:

    def test_missing_id_token_returns_422(self, client):
        resp = client.post("/api/v1/auth/google", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /me – auth contract
# ---------------------------------------------------------------------------


class TestGetMe:
    """GET /api/v1/auth/me returns current user info."""

    def test_authenticated_returns_200(self, client, test_user):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == test_user.email
        assert "id" in data
        assert "auth_provider" in data

    def test_unauthenticated_returns_401(self, unauthed_client):
        resp = unauthed_client.get("/api/v1/auth/me")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /refresh – requires Bearer header
# ---------------------------------------------------------------------------


class TestRefreshEndpoint:
    """POST /api/v1/auth/refresh requires Authorization: Bearer <refresh>."""

    def test_no_auth_header_returns_403(self, unauthed_client):
        resp = unauthed_client.post("/api/v1/auth/refresh")
        assert resp.status_code in (401, 403)
