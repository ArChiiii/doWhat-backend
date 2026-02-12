"""
Shared fixtures for unit tests.

Uses FastAPI TestClient with dependency overrides (mocked DB and services)
so tests run without PostgreSQL/Redis/Supabase.
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.dependencies import get_current_user, get_current_user_optional
from app.models.user import User
from app.services.auth_service import AuthService


# ---------------------------------------------------------------------------
# Fake user for authenticated requests
# ---------------------------------------------------------------------------

TEST_USER_ID = uuid.uuid4()
TEST_USER_EMAIL = "unit@dowhat.com"


def _make_test_user() -> User:
    """Return a User ORM-like object with default test attributes."""
    user = MagicMock(spec=User)
    user.id = TEST_USER_ID
    user.email = TEST_USER_EMAIL
    user.email_verified = False
    user.auth_provider = "email"
    user.auth_provider_id = None
    user.created_at = datetime(2025, 1, 1)
    user.updated_at = datetime(2025, 1, 1)
    user.last_login_at = datetime(2025, 6, 1)
    return user


# ---------------------------------------------------------------------------
# Dependency overrides
# ---------------------------------------------------------------------------


def _override_get_db():
    """Yield a MagicMock session so no real DB is required."""
    db = MagicMock()
    try:
        yield db
    finally:
        pass


def _override_get_current_user() -> User:
    return _make_test_user()


def _override_get_current_user_optional():
    return _make_test_user()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def test_user():
    """A mock User object for assertions."""
    return _make_test_user()


@pytest.fixture()
def client():
    """
    FastAPI TestClient with dependency overrides.

    All DB/auth dependencies are mocked so tests exercise the router
    layer (request validation, status codes, response schemas) without
    external services.
    """
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    app.dependency_overrides[get_current_user_optional] = _override_get_current_user_optional

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture()
def unauthed_client():
    """
    TestClient where get_current_user raises 403/401 and
    get_current_user_optional returns None (guest user).
    """
    from fastapi import HTTPException, status

    def _raise_unauthed():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    def _return_none():
        return None

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _raise_unauthed
    app.dependency_overrides[get_current_user_optional] = _return_none

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture()
def mock_db():
    """Standalone mock DB session for service-level tests."""
    return MagicMock()


@pytest.fixture()
def auth_tokens(test_user):
    """Generate real JWT tokens for the test user (local-dev path)."""
    svc = AuthService()
    access = svc.create_access_token(
        data={"sub": str(test_user.id), "email": test_user.email}
    )
    refresh = svc.create_refresh_token(data={"sub": str(test_user.id)})
    return {"access_token": access, "refresh_token": refresh}
