#!/usr/bin/env python3
"""
Pytest-based integration tests for doWhat backend.

Hits the real Docker-hosted API on localhost:8000.
Run with: pytest tests/test_api_endpoints.py -v

Tests include:
1. API server reachability
2. Health check endpoint
3. API status endpoint
4. User registration
5. User login
6. Token refresh
7. GET /me
8. Event feed
9. Map events
10. Event detail
11. Swipe recording
12. Saved events CRUD
13. Connection stability
14. Error handling
"""

import pytest
import requests
import time
from typing import Dict, Any, Optional


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api_base_url():
    """Base URL for API testing."""
    return "http://localhost:8000"


@pytest.fixture
def api_client(api_base_url):
    """HTTP client for API requests."""

    class APIClient:
        def __init__(self, base_url: str):
            self.base_url = base_url

        def make_request(
            self,
            method: str,
            endpoint: str,
            data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, Any]] = None,
            timeout: int = 10,
        ) -> Optional[requests.Response]:
            """Make HTTP request to API."""
            url = f"{self.base_url}{endpoint}"
            try:
                method_upper = method.upper()
                if method_upper == "GET":
                    response = requests.get(
                        url, headers=headers, params=params, timeout=timeout
                    )
                elif method_upper == "POST":
                    response = requests.post(
                        url, json=data, headers=headers, params=params, timeout=timeout
                    )
                elif method_upper == "DELETE":
                    response = requests.delete(
                        url, headers=headers, params=params, timeout=timeout
                    )
                elif method_upper == "PUT":
                    response = requests.put(
                        url, json=data, headers=headers, params=params, timeout=timeout
                    )
                elif method_upper == "PATCH":
                    response = requests.patch(
                        url, json=data, headers=headers, params=params, timeout=timeout
                    )
                else:
                    raise ValueError(f"Unsupported method: {method}")

                return response

            except requests.exceptions.ConnectionError:
                pytest.fail(f"Connection failed: Cannot reach {self.base_url}")
            except requests.exceptions.Timeout:
                pytest.fail(f"Request timeout after {timeout}s")
            except Exception as e:
                pytest.fail(f"Request failed: {str(e)}")

    return APIClient(api_base_url)


@pytest.fixture
def test_user_data():
    """Generate unique test user data for each test run."""
    timestamp = int(time.time())
    return {
        "email": f"test_user_{timestamp}@dowhat.com",
        "password": "TestPassword123!",
    }


@pytest.fixture
def auth_headers(api_client, test_user_data):
    """
    Register a fresh user and return Authorization headers with access token.
    Validates the token actually works with /api/v1/auth/me; skips if the
    backend uses Supabase-signed tokens (which can't be verified locally).
    """
    reg = api_client.make_request(
        "POST", "/api/v1/auth/register", data=test_user_data
    )
    if reg.status_code != 201:
        pytest.skip("Could not register test user (possibly duplicate)")

    data = reg.json()
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify the token is accepted by the backend
    me = api_client.make_request("GET", "/api/v1/auth/me", headers=headers)
    if me.status_code == 401:
        pytest.skip(
            "Supabase-signed tokens cannot be verified by local JWT — "
            "run with local-dev auth (no SUPABASE_URL) for full coverage"
        )

    return {
        "Authorization": f"Bearer {token}",
        "_auth_data": data,
    }


@pytest.fixture
def auth_tokens(api_client, test_user_data):
    """
    Register user and return both access + refresh tokens.
    Validates the access token works; skips on Supabase token mismatch.
    """
    reg = api_client.make_request(
        "POST", "/api/v1/auth/register", data=test_user_data
    )
    if reg.status_code != 201:
        pytest.skip("Could not register test user")
    data = reg.json()

    # Verify the token is usable
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    me = api_client.make_request("GET", "/api/v1/auth/me", headers=headers)
    if me.status_code == 401:
        pytest.skip(
            "Supabase-signed tokens cannot be verified by local JWT — "
            "run with local-dev auth for full coverage"
        )

    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }


# =====================================================================
# 1. Server Reachability
# =====================================================================


class TestAPIServerReachability:
    """Test API server basic connectivity."""

    @pytest.mark.unit
    def test_api_server_reachable(self, api_client):
        """Test that API server is reachable and returns basic info."""
        response = api_client.make_request("GET", "/")

        assert response is not None
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "environment" in data
        assert "status" in data


# =====================================================================
# 2. Health Check
# =====================================================================


class TestHealthCheck:
    """Test health check endpoint."""

    @pytest.mark.unit
    def test_health_check_endpoint(self, api_client):
        """Test health check endpoint returns valid response."""
        response = api_client.make_request("GET", "/health")

        assert response is not None
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "timestamp" in data
        assert "database" in data


# =====================================================================
# 3. API Status
# =====================================================================


class TestAPIStatus:
    """Test API status endpoint."""

    @pytest.mark.unit
    def test_api_status_endpoint(self, api_client):
        """Test API status endpoint returns version and endpoint info."""
        response = api_client.make_request("GET", "/api/v1/status")

        assert response is not None
        assert response.status_code == 200

        data = response.json()
        assert "api_version" in data
        assert "status" in data
        assert "endpoints" in data
        assert isinstance(data["endpoints"], dict)


# =====================================================================
# 4. User Registration
# =====================================================================


class TestUserRegistration:
    """Test user registration endpoint."""

    @pytest.mark.integration
    def test_user_registration_success(self, api_client, test_user_data):
        """Test successful user registration."""
        response = api_client.make_request(
            "POST", "/api/v1/auth/register", data=test_user_data
        )

        assert response is not None

        # Should either succeed (201) or handle duplicate (409)
        assert response.status_code in [201, 409]

        if response.status_code == 201:
            data = response.json()
            assert "user" in data
            assert "access_token" in data
            assert "refresh_token" in data

            user = data["user"]
            assert user["email"] == test_user_data["email"]
            assert "id" in user
            assert "auth_provider" in user
            assert "email_verified" in user

    @pytest.mark.integration
    def test_user_registration_duplicate_email(self, api_client, test_user_data):
        """Test registration with duplicate email is handled properly."""
        # First registration
        api_client.make_request("POST", "/api/v1/auth/register", data=test_user_data)

        # Second registration with same email
        response2 = api_client.make_request(
            "POST", "/api/v1/auth/register", data=test_user_data
        )

        assert response2 is not None
        assert response2.status_code == 409  # Conflict

    @pytest.mark.unit
    def test_user_registration_validation_error(self, api_client):
        """Test registration with invalid data returns validation error."""
        invalid_data = {"email": "invalid-email", "password": "123"}  # Too short

        response = api_client.make_request(
            "POST", "/api/v1/auth/register", data=invalid_data
        )

        assert response is not None
        assert response.status_code == 422  # Validation error


# =====================================================================
# 5. User Login
# =====================================================================


class TestUserLogin:
    """Test user login endpoint."""

    @pytest.mark.integration
    def test_user_login_success(self, api_client, test_user_data):
        """Test successful user login after registration."""
        # First register a user
        reg_response = api_client.make_request(
            "POST", "/api/v1/auth/register", data=test_user_data
        )

        if reg_response.status_code == 201:
            # Then login
            login_response = api_client.make_request(
                "POST", "/api/v1/auth/login", data=test_user_data
            )

            assert login_response is not None
            assert login_response.status_code == 200

            data = login_response.json()
            assert "user" in data
            assert "access_token" in data

            user = data["user"]
            assert user["email"] == test_user_data["email"]
            assert "id" in user
            assert "last_login_at" in user

    @pytest.mark.unit
    def test_user_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials returns 401."""
        invalid_credentials = {
            "email": "nonexistent@dowhat.com",
            "password": "wrongpassword",
        }

        response = api_client.make_request(
            "POST", "/api/v1/auth/login", data=invalid_credentials
        )

        assert response is not None
        assert response.status_code == 401

    @pytest.mark.unit
    def test_user_login_validation_error(self, api_client):
        """Test login with invalid data returns validation error."""
        invalid_data = {"email": "invalid-email", "password": ""}  # Empty password

        response = api_client.make_request(
            "POST", "/api/v1/auth/login", data=invalid_data
        )

        assert response is not None
        assert response.status_code == 422  # Validation error


# =====================================================================
# 6. Token Refresh
# =====================================================================


class TestTokenRefresh:
    """Test token refresh endpoint."""

    @pytest.mark.integration
    def test_refresh_with_valid_token(self, api_client, auth_tokens):
        """Refresh endpoint returns new access token."""
        headers = {"Authorization": f"Bearer {auth_tokens['refresh_token']}"}
        resp = api_client.make_request("POST", "/api/v1/auth/refresh", headers=headers)

        assert resp is not None
        assert resp.status_code == 200

        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.unit
    def test_refresh_without_token_returns_error(self, api_client):
        """Refresh without Authorization header returns 401/403."""
        resp = api_client.make_request("POST", "/api/v1/auth/refresh")
        assert resp is not None
        assert resp.status_code in (401, 403)

    @pytest.mark.unit
    def test_refresh_with_bad_token(self, api_client):
        """Refresh with garbage token returns 401."""
        headers = {"Authorization": "Bearer obviously-bad-token"}
        resp = api_client.make_request("POST", "/api/v1/auth/refresh", headers=headers)
        assert resp is not None
        assert resp.status_code == 401


# =====================================================================
# 7. GET /me
# =====================================================================


class TestGetMe:
    """Test GET /api/v1/auth/me."""

    @pytest.mark.integration
    def test_me_returns_user_info(self, api_client, auth_headers):
        """Authenticated user gets their own profile."""
        headers = {"Authorization": auth_headers["Authorization"]}
        resp = api_client.make_request("GET", "/api/v1/auth/me", headers=headers)

        assert resp is not None
        assert resp.status_code == 200

        data = resp.json()
        assert "id" in data
        assert "email" in data
        assert "auth_provider" in data

    @pytest.mark.unit
    def test_me_without_auth_returns_error(self, api_client):
        """Unauthenticated request to /me returns 401/403."""
        resp = api_client.make_request("GET", "/api/v1/auth/me")
        assert resp is not None
        assert resp.status_code in (401, 403)


# =====================================================================
# 8. Event Feed
# =====================================================================


class TestEventFeed:
    """Test GET /api/v1/events/feed."""

    @pytest.mark.integration
    def test_feed_returns_200(self, api_client):
        """Feed endpoint returns valid paginated response."""
        resp = api_client.make_request("GET", "/api/v1/events/feed")
        assert resp is not None
        assert resp.status_code == 200

        data = resp.json()
        assert "events" in data
        assert "count" in data
        assert "total" in data
        assert isinstance(data["events"], list)

    @pytest.mark.integration
    def test_feed_pagination(self, api_client):
        """Feed respects page and limit params."""
        resp = api_client.make_request(
            "GET", "/api/v1/events/feed",
            params={"page": 1, "limit": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["events"]) <= 5

    @pytest.mark.unit
    def test_feed_invalid_page_returns_422(self, api_client):
        resp = api_client.make_request(
            "GET", "/api/v1/events/feed",
            params={"page": 0},
        )
        assert resp.status_code == 422

    @pytest.mark.integration
    def test_feed_with_category_filter(self, api_client):
        resp = api_client.make_request(
            "GET", "/api/v1/events/feed",
            params={"categories": "music"},
        )
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_feed_with_time_filter(self, api_client):
        resp = api_client.make_request(
            "GET", "/api/v1/events/feed",
            params={"time_filter": "week"},
        )
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_feed_authenticated_marks_saved(self, api_client, auth_headers):
        """Authenticated feed includes isSaved flag."""
        headers = {"Authorization": auth_headers["Authorization"]}
        resp = api_client.make_request(
            "GET", "/api/v1/events/feed", headers=headers
        )
        assert resp.status_code == 200
        # All events should have isSaved field
        for ev in resp.json()["events"]:
            assert "isSaved" in ev


# =====================================================================
# 9. Map Events
# =====================================================================


class TestMapEvents:
    """Test GET /api/v1/events/map."""

    @pytest.mark.integration
    def test_map_returns_200(self, api_client):
        resp = api_client.make_request("GET", "/api/v1/events/map")
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data
        assert "count" in data

    @pytest.mark.integration
    def test_map_with_location(self, api_client):
        """Map endpoint filters by lat/lng/radius."""
        resp = api_client.make_request(
            "GET", "/api/v1/events/map",
            params={"lat": 22.28, "lng": 114.16, "radius": 10000},
        )
        assert resp.status_code == 200


# =====================================================================
# 10. Event Detail
# =====================================================================


class TestEventDetail:
    """Test GET /api/v1/events/{event_id}."""

    @pytest.mark.integration
    def test_nonexistent_event_returns_404(self, api_client):
        """Requesting a random UUID returns 404."""
        import uuid
        fake_id = str(uuid.uuid4())
        resp = api_client.make_request("GET", f"/api/v1/events/{fake_id}")
        assert resp.status_code == 404

    @pytest.mark.integration
    def test_real_event_if_available(self, api_client):
        """If feed has events, fetching one by ID returns 200."""
        feed = api_client.make_request(
            "GET", "/api/v1/events/feed", params={"limit": 1}
        )
        events = feed.json().get("events", [])
        if not events:
            pytest.skip("No events in feed to test detail endpoint")
        eid = events[0]["id"]
        resp = api_client.make_request("GET", f"/api/v1/events/{eid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == eid
        assert "title" in data
        assert "venue" in data


# =====================================================================
# 11. Swipe
# =====================================================================


class TestSwipe:
    """Test POST /api/v1/events/{event_id}/swipe."""

    @pytest.mark.unit
    def test_swipe_requires_auth(self, api_client):
        import uuid
        eid = str(uuid.uuid4())
        resp = api_client.make_request(
            "POST", f"/api/v1/events/{eid}/swipe",
            data={"direction": "right"},
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.unit
    def test_swipe_invalid_direction(self, api_client, auth_headers):
        import uuid
        eid = str(uuid.uuid4())
        headers = {"Authorization": auth_headers["Authorization"]}
        resp = api_client.make_request(
            "POST", f"/api/v1/events/{eid}/swipe",
            data={"direction": "up"},
            headers=headers,
        )
        assert resp.status_code == 422

    @pytest.mark.integration
    def test_swipe_on_real_event(self, api_client, auth_headers):
        """Swipe right on a real event from the feed."""
        feed = api_client.make_request(
            "GET", "/api/v1/events/feed", params={"limit": 1}
        )
        events = feed.json().get("events", [])
        if not events:
            pytest.skip("No events in feed")
        eid = events[0]["id"]
        headers = {"Authorization": auth_headers["Authorization"]}
        resp = api_client.make_request(
            "POST", f"/api/v1/events/{eid}/swipe",
            data={"direction": "right"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True


# =====================================================================
# 12. Saved Events CRUD
# =====================================================================


class TestSavedEventsCRUD:
    """Test saved events list/save/unsave cycle."""

    @pytest.mark.integration
    def test_list_saved_requires_auth(self, api_client):
        resp = api_client.make_request("GET", "/api/v1/users/saved-events/")
        assert resp.status_code in (401, 403)

    @pytest.mark.integration
    def test_list_saved_empty(self, api_client, auth_headers):
        """New user has no saved events."""
        headers = {"Authorization": auth_headers["Authorization"]}
        resp = api_client.make_request(
            "GET", "/api/v1/users/saved-events/", headers=headers
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.integration
    def test_save_and_unsave_cycle(self, api_client, auth_headers):
        """Save an event, verify it appears, unsave it."""
        headers = {"Authorization": auth_headers["Authorization"]}

        # Get an event from the feed
        feed = api_client.make_request(
            "GET", "/api/v1/events/feed", params={"limit": 1}
        )
        events = feed.json().get("events", [])
        if not events:
            pytest.skip("No events in feed")
        eid = events[0]["id"]

        # Save
        save_resp = api_client.make_request(
            "POST", f"/api/v1/users/saved-events/{eid}", headers=headers
        )
        assert save_resp.status_code == 200
        assert save_resp.json()["success"] is True

        # Verify in list
        list_resp = api_client.make_request(
            "GET", "/api/v1/users/saved-events/", headers=headers
        )
        assert list_resp.status_code == 200
        ids = [e["id"] for e in list_resp.json()]
        assert eid in ids

        # Unsave
        unsave_resp = api_client.make_request(
            "DELETE", f"/api/v1/users/saved-events/{eid}", headers=headers
        )
        assert unsave_resp.status_code == 200
        assert unsave_resp.json()["success"] is True

    @pytest.mark.integration
    def test_save_idempotent(self, api_client, auth_headers):
        """Saving the same event twice succeeds both times."""
        headers = {"Authorization": auth_headers["Authorization"]}
        feed = api_client.make_request(
            "GET", "/api/v1/events/feed", params={"limit": 1}
        )
        events = feed.json().get("events", [])
        if not events:
            pytest.skip("No events in feed")
        eid = events[0]["id"]

        r1 = api_client.make_request(
            "POST", f"/api/v1/users/saved-events/{eid}", headers=headers
        )
        r2 = api_client.make_request(
            "POST", f"/api/v1/users/saved-events/{eid}", headers=headers
        )
        assert r1.status_code == 200
        assert r2.status_code == 200

    @pytest.mark.integration
    def test_unsave_nonexistent_returns_404(self, api_client, auth_headers):
        """Unsaving an event never saved returns 404."""
        import uuid
        headers = {"Authorization": auth_headers["Authorization"]}
        fake_id = str(uuid.uuid4())
        resp = api_client.make_request(
            "DELETE", f"/api/v1/users/saved-events/{fake_id}", headers=headers
        )
        assert resp.status_code == 404


# =====================================================================
# 13. Connection Stability
# =====================================================================


class TestConnectionStability:
    """Test API connection stability."""

    @pytest.mark.slow
    def test_connection_stability_multiple_requests(self, api_client):
        """Test that multiple consecutive requests work reliably."""
        success_count = 0
        total_requests = 10

        for i in range(total_requests):
            response = api_client.make_request("GET", "/health")

            if response and response.status_code == 200:
                success_count += 1

            time.sleep(0.1)  # Small delay between requests

        # At least 80% of requests should succeed
        success_rate = success_count / total_requests
        assert (
            success_rate >= 0.8
        ), f"Only {success_rate*100:.1f}% of requests succeeded"

    @pytest.mark.unit
    def test_health_endpoint_response_time(self, api_client):
        """Test that health endpoint responds within reasonable time."""
        start_time = time.time()
        response = api_client.make_request("GET", "/health")
        elapsed_time = time.time() - start_time

        assert response is not None
        assert response.status_code == 200
        assert (
            elapsed_time < 2.0
        ), f"Health endpoint took {elapsed_time:.2f}s (too slow)"


# =====================================================================
# 14. Error Handling
# =====================================================================


class TestAPIErrorHandling:
    """Test API error handling and edge cases."""

    @pytest.mark.unit
    def test_nonexistent_endpoint_returns_404(self, api_client):
        """Test that nonexistent endpoints return 404."""
        response = api_client.make_request("GET", "/api/v1/nonexistent")

        assert response is not None
        assert response.status_code == 404

    @pytest.mark.unit
    def test_invalid_http_method_returns_405(self, api_client):
        """Test that invalid HTTP methods return 405."""
        # Try to GET a POST-only endpoint
        response = api_client.make_request("GET", "/api/v1/auth/register")

        assert response is not None
        assert response.status_code == 405

    @pytest.mark.unit
    def test_malformed_json_returns_422(self, api_client):
        """Test that malformed JSON returns appropriate error."""
        incomplete_data = {"email": "test@dowhat.com"}  # Missing password

        response = api_client.make_request(
            "POST", "/api/v1/auth/register", data=incomplete_data
        )

        assert response is not None
        assert response.status_code == 422


# =====================================================================
# Pytest hooks (marker config)
# =====================================================================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line(
        "markers", "integration: Integration tests (slower, external dependencies)"
    )
    config.addinivalue_line("markers", "slow: Tests that take a long time to run")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add slow marker to stability tests
        if "stability" in item.name:
            item.add_marker(pytest.mark.slow)

        # Add integration marker to auth tests
        if "login" in item.name or "registration" in item.name:
            item.add_marker(pytest.mark.integration)
