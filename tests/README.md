# API Endpoint Tests

This directory contains pytest-based tests for the doWhat backend API endpoints.

## Test Files

### `test_api_endpoints.py`
Comprehensive API endpoint testing focused on HTTP functionality without database connection testing.

**Test Categories:**
- **Unit Tests** (`@pytest.mark.unit`): Fast, isolated tests
- **Integration Tests** (`@pytest.mark.integration`): Tests with external dependencies
- **Slow Tests** (`@pytest.mark.slow`): Tests that take longer to run

**Test Classes:**
- `TestAPIServerReachability`: Basic server connectivity
- `TestHealthCheck`: Health check endpoint validation
- `TestAPIStatus`: API status and version information
- `TestUserRegistration`: User registration endpoint testing
- `TestUserLogin`: User authentication testing
- `TestConnectionStability`: API reliability and performance
- `TestAPIErrorHandling`: Error response validation

## Running Tests

### Prerequisites
1. Start the API server: `docker-compose up`
2. Ensure the server is running on `http://localhost:8000`

### Basic Test Execution
```bash
# Run all tests
pytest tests/test_api_endpoints.py -v

# Run only unit tests (fast)
pytest tests/test_api_endpoints.py -m unit -v

# Run only integration tests
pytest tests/test_api_endpoints.py -m integration -v

# Skip slow tests
pytest tests/test_api_endpoints.py -m "not slow" -v

# Run with coverage
pytest tests/test_api_endpoints.py --cov=app --cov-report=html
```

### Test Markers
- `unit`: Fast, isolated tests
- `integration`: Tests with external dependencies
- `slow`: Tests that take a long time to run
- `auth`: Authentication-related tests

### Example Output
```
========================= test session starts =========================
collected 12 items

tests/test_api_endpoints.py::TestAPIServerReachability::test_api_server_reachable PASSED
tests/test_api_endpoints.py::TestHealthCheck::test_health_check_endpoint PASSED
tests/test_api_endpoints.py::TestAPIStatus::test_api_status_endpoint PASSED
tests/test_api_endpoints.py::TestUserRegistration::test_user_registration_success PASSED
tests/test_api_endpoints.py::TestUserLogin::test_user_login_success PASSED
tests/test_api_endpoints.py::TestConnectionStability::test_health_endpoint_response_time PASSED
tests/test_api_endpoints.py::TestAPIErrorHandling::test_nonexistent_endpoint_returns_404 PASSED
tests/test_api_endpoints.py::TestAPIErrorHandling::test_invalid_http_method_returns_405 PASSED
tests/test_api_endpoints.py::TestAPIErrorHandling::test_malformed_json_returns_422 PASSED

========================= 9 passed in 2.34s =========================
```

## Test Configuration

The tests use pytest fixtures for:
- `api_base_url`: Configurable API base URL (default: http://localhost:8000)
- `api_client`: HTTP client for making requests
- `test_user_data`: Unique test user data for each test run

## Differences from Manual Test

This pytest version differs from the original `manual_api_test.py`:

1. **No Database Connection Testing**: Focuses purely on API endpoint functionality
2. **Structured Test Classes**: Organized by functionality for better maintainability
3. **Pytest Fixtures**: Reusable test components and configuration
4. **Test Markers**: Categorization for selective test execution
5. **Standard Assertions**: Uses pytest's assertion system instead of custom reporting
6. **Parallel Execution**: Can run tests in parallel for faster execution

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure the API server is running
   ```bash
   docker-compose up
   ```

2. **Test Failures**: Check server logs for detailed error information
   ```bash
   docker-compose logs backend
   ```

3. **Slow Tests**: Use markers to skip slow tests during development
   ```bash
   pytest tests/test_api_endpoints.py -m "not slow" -v
   ```

### Environment Variables
Tests can be configured using environment variables:
- `API_BASE_URL`: Override the default API base URL
- `TEST_TIMEOUT`: Override the default request timeout
