"""
Pytest configuration and shared fixtures for doWhat backend tests.
"""

import pytest
import os
from typing import Generator


@pytest.fixture(scope="session")
def test_environment():
    """Set up test environment variables."""
    # Ensure we're using test environment
    os.environ.setdefault("ENVIRONMENT", "test")
    return "test"


@pytest.fixture(scope="session")
def api_timeout():
    """Default timeout for API requests in tests."""
    return 10


@pytest.fixture(autouse=True)
def setup_test_environment(test_environment):
    """Automatically set up test environment for each test."""
    # This fixture runs before each test
    yield
    # Cleanup after each test (if needed)
    pass


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line(
        "markers", "integration: Integration tests (slower, external dependencies)"
    )
    config.addinivalue_line("markers", "auth: Authentication-related tests")
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
            item.add_marker(pytest.mark.auth)
