#!/usr/bin/env python3
"""
Pytest-based API endpoint testing for doWhat backend.

This test suite focuses on API endpoint functionality without database
connection testing. Tests include:
1. API server reachability
2. Health check endpoint
3. API status endpoint
4. User registration endpoint
5. User login endpoint
6. Connection stability

Run with: pytest tests/test_api_endpoints.py -v
"""

import pytest
import requests
import time
from typing import Dict, Any, Optional


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
            timeout: int = 10,
        ) -> Optional[requests.Response]:
            """Make HTTP request to API."""
            url = f"{self.base_url}{endpoint}"
            try:
                if method.upper() == "GET":
                    response = requests.get(url, headers=headers, timeout=timeout)
                elif method.upper() == "POST":
                    response = requests.post(
                        url, json=data, headers=headers, timeout=timeout
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
        # This test would require sending raw malformed JSON
        # For now, we'll test with missing required fields
        incomplete_data = {"email": "test@dowhat.com"}  # Missing password

        response = api_client.make_request(
            "POST", "/api/v1/auth/register", data=incomplete_data
        )

        assert response is not None
        assert response.status_code == 422


# Utility functions for test reporting
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
