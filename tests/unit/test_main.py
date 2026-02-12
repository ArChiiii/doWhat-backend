"""
Unit tests for root-level endpoints defined in app/main.py:
  /          – root
  /health    – health check
  /api/v1/status – API status
  404 / 500 error handlers
"""

import pytest


class TestRootEndpoint:
    """GET /"""

    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_root_contains_required_fields(self, client):
        data = client.get("/").json()
        assert "message" in data
        assert "status" in data
        assert "environment" in data

    def test_root_status_is_healthy(self, client):
        data = client.get("/").json()
        assert data["status"] == "healthy"


class TestHealthCheck:
    """GET /health"""

    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_contains_required_fields(self, client):
        data = client.get("/health").json()
        for key in ("status", "service", "timestamp", "version", "environment"):
            assert key in data, f"Missing key: {key}"

    def test_health_reports_database_field(self, client):
        data = client.get("/health").json()
        assert "database" in data


class TestAPIStatus:
    """GET /api/v1/status"""

    def test_status_returns_200(self, client):
        resp = client.get("/api/v1/status")
        assert resp.status_code == 200

    def test_status_has_required_fields(self, client):
        data = client.get("/api/v1/status").json()
        assert data["api_version"] == "v1"
        assert data["status"] == "operational"
        assert isinstance(data["endpoints"], dict)

    def test_status_lists_expected_endpoint_groups(self, client):
        endpoints = client.get("/api/v1/status").json()["endpoints"]
        for group in ("auth", "events", "users"):
            assert group in endpoints


class TestErrorHandlers:
    """404 and unknown-route behaviour."""

    def test_unknown_route_returns_404(self, client):
        resp = client.get("/api/v1/does-not-exist")
        assert resp.status_code == 404

    def test_404_body_has_error_and_message(self, client):
        data = client.get("/api/v1/does-not-exist").json()
        assert "error" in data
        assert "message" in data

    def test_wrong_method_returns_405(self, client):
        resp = client.get("/api/v1/auth/register")
        assert resp.status_code == 405
