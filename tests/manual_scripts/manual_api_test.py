#!/usr/bin/env python3
"""
Manual API Testing Script for Database Connection Validation

This script performs manual API endpoint testing to verify:
1. API server starts successfully
2. Health check endpoint returns database connected status
3. User registration endpoint works correctly
4. Database operations succeed without connection errors

Run this script with: python tests/manual_api_test.py
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class APITester:
    """API testing utility class."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.start_time = None

    def print_header(self, text: str):
        """Print a formatted header."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")

    def print_success(self, text: str):
        """Print success message."""
        print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

    def print_error(self, text: str):
        """Print error message."""
        print(f"{Colors.RED}✗ {text}{Colors.RESET}")

    def print_warning(self, text: str):
        """Print warning message."""
        print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

    def print_info(self, text: str):
        """Print info message."""
        print(f"  {text}")

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
            self.print_error(f"Connection failed: Cannot reach {self.base_url}")
            self.print_info("Make sure the API server is running: docker-compose up")
            return None
        except requests.exceptions.Timeout:
            self.print_error(f"Request timeout after {timeout}s")
            return None
        except Exception as e:
            self.print_error(f"Request failed: {str(e)}")
            return None

    def test_api_server_reachable(self) -> bool:
        """Test 1: API server is reachable."""
        self.print_header("TEST 1: API Server Reachability")

        response = self.make_request("GET", "/")

        if response is None:
            self.print_error("API server is not reachable")
            self.test_results.append(
                ("API Server Reachable", False, "Connection failed")
            )
            return False

        if response.status_code == 200:
            data = response.json()
            self.print_success(f"API server is running")
            self.print_info(f"Service: {data.get('message', 'N/A')}")
            self.print_info(f"Environment: {data.get('environment', 'N/A')}")
            self.print_info(f"Status: {data.get('status', 'N/A')}")
            self.test_results.append(("API Server Reachable", True, "OK"))
            return True
        else:
            self.print_error(f"Unexpected status code: {response.status_code}")
            self.test_results.append(
                ("API Server Reachable", False, f"Status {response.status_code}")
            )
            return False

    def test_health_check(self) -> bool:
        """Test 2: Health check endpoint with database status."""
        self.print_header("TEST 2: Health Check - Database Connection")

        response = self.make_request("GET", "/health")

        if response is None:
            self.test_results.append(("Health Check", False, "Connection failed"))
            return False

        if response.status_code == 200:
            data = response.json()
            print(data)
            db_status = data.get("database", "unknown")

            self.print_info(f"Overall Status: {data.get('status', 'N/A')}")
            self.print_info(f"Service: {data.get('service', 'N/A')}")
            self.print_info(f"Timestamp: {data.get('timestamp', 'N/A')}")

            if db_status == "connected":
                self.print_success(f"Database Status: {db_status}")
                self.test_results.append(("Database Connection", True, "Connected"))
                return True
            elif "error" in db_status:
                self.print_error(f"Database Status: {db_status}")
                self.test_results.append(("Database Connection", False, db_status))
                return False
            else:
                self.print_warning(f"Database Status: {db_status}")
                self.test_results.append(("Database Connection", False, db_status))
                return False
        else:
            self.print_error(f"Health check failed with status {response.status_code}")
            self.test_results.append(
                ("Health Check", False, f"Status {response.status_code}")
            )
            return False

    def test_api_status(self) -> bool:
        """Test 3: API status endpoint."""
        self.print_header("TEST 3: API Status Endpoint")

        response = self.make_request("GET", "/api/v1/status")

        if response is None:
            self.test_results.append(("API Status", False, "Connection failed"))
            return False

        if response.status_code == 200:
            data = response.json()
            self.print_success("API status endpoint working")
            self.print_info(f"API Version: {data.get('api_version', 'N/A')}")
            self.print_info(f"Status: {data.get('status', 'N/A')}")

            endpoints = data.get("endpoints", {})
            for name, path in endpoints.items():
                self.print_info(f"  - {name}: {path}")

            self.test_results.append(("API Status", True, "OK"))
            return True
        else:
            self.print_error(
                f"API status check failed with status {response.status_code}"
            )
            self.test_results.append(
                ("API Status", False, f"Status {response.status_code}")
            )
            return False

    def test_user_registration(self) -> bool:
        """Test 4: User registration endpoint (tests database write)."""
        self.print_header("TEST 4: User Registration (Database Write Test)")

        # Generate unique email for this test
        timestamp = int(time.time())
        test_email = f"test_user_{timestamp}@dowhat.com"
        test_password = "TestPassword123!"

        test_user = {
            "email": test_email,
            "password": test_password,
        }

        self.print_info(f"Registering test user: {test_email}")

        response = self.make_request("POST", "/api/v1/auth/register", data=test_user)

        if response is None:
            self.test_results.append(("User Registration", False, "Connection failed"))
            return None, None

        if response.status_code == 201:
            data = response.json()
            self.print_success("User registered successfully")

            user = data.get("user", {})
            self.print_info(f"User ID: {user.get('id', 'N/A')}")
            self.print_info(f"Email: {user.get('email', 'N/A')}")
            self.print_info(f"Auth Provider: {user.get('auth_provider', 'N/A')}")
            self.print_info(f"Email Verified: {user.get('email_verified', 'N/A')}")

            # Verify tokens were returned
            if "access_token" in data and "refresh_token" in data:
                self.print_success("Access and refresh tokens returned")
                self.test_results.append(("User Registration", True, "OK"))
                return test_email, test_password
            else:
                self.print_warning("Tokens missing from response")
                self.test_results.append(("User Registration", False, "Missing tokens"))
                return None, None

        elif response.status_code == 409:
            self.print_warning("Email already registered (expected if test ran before)")
            self.print_info("This is not a failure - registration endpoint is working")
            self.test_results.append(
                ("User Registration", True, "Duplicate email handled")
            )
            return None, None

        elif response.status_code == 422:
            self.print_error("Validation error")
            self.print_info(f"Response: {response.json()}")
            self.test_results.append(("User Registration", False, "Validation error"))
            return None, None

        elif response.status_code == 500:
            data = response.json()
            error_detail = data.get("detail", "Unknown error")
            self.print_error(f"Internal server error: {error_detail}")

            # Check if it's a database connection error
            if "Cannot assign requested address" in error_detail:
                self.print_error("DATABASE CONNECTION ERROR - IPv6/IPv4 issue detected")
                self.test_results.append(
                    ("User Registration", False, "DB connection error")
                )
            else:
                self.test_results.append(("User Registration", False, error_detail))

            return None, None

        else:
            self.print_error(f"Unexpected status code: {response.status_code}")
            self.print_info(f"Response: {response.text}")
            self.test_results.append(
                ("User Registration", False, f"Status {response.status_code}")
            )
            return None, None

    def test_user_login(self, email: str, password: str) -> Optional[str]:
        """Test 5: User login endpoint (tests database read)."""
        self.print_header("TEST 5: User Login (Database Read Test)")

        login_data = {"email": email, "password": password}

        self.print_info(f"Logging in as: {email}")

        response = self.make_request("POST", "/api/v1/auth/login", data=login_data)

        if response is None:
            self.test_results.append(("User Login", False, "Connection failed"))
            return None

        if response.status_code == 200:
            data = response.json()
            self.print_success("Login successful")

            user = data.get("user", {})
            self.print_info(f"User ID: {user.get('id', 'N/A')}")
            self.print_info(f"Last Login: {user.get('last_login_at', 'N/A')}")

            access_token = data.get("access_token")
            if access_token:
                self.print_success("Access token received")
                self.test_results.append(("User Login", True, "OK"))
                return access_token
            else:
                self.print_error("No access token in response")
                self.test_results.append(("User Login", False, "Missing token"))
                return None

        elif response.status_code == 401:
            self.print_error("Invalid credentials")
            self.print_info("User may not exist - run registration test first")
            self.test_results.append(("User Login", False, "Invalid credentials"))
            return None

        else:
            self.print_error(f"Login failed with status {response.status_code}")
            self.test_results.append(
                ("User Login", False, f"Status {response.status_code}")
            )
            return None

    def test_connection_stability(self) -> bool:
        """Test 6: Connection stability (multiple requests)."""
        self.print_header("TEST 6: Connection Stability (10 requests)")

        success_count = 0
        failure_count = 0
        total_time = 0

        for i in range(10):
            start = time.time()
            response = self.make_request("GET", "/health")
            elapsed = time.time() - start

            if response and response.status_code == 200:
                data = response.json()
                if data.get("database") == "connected":
                    success_count += 1
                    total_time += elapsed
                    print(f"  Request {i+1}/10: OK ({elapsed*1000:.0f}ms)")
                else:
                    failure_count += 1
                    print(f"  Request {i+1}/10: FAILED - DB not connected")
            else:
                failure_count += 1
                print(f"  Request {i+1}/10: FAILED")

            time.sleep(0.1)  # Small delay between requests

        if failure_count == 0:
            avg_time = total_time / success_count
            self.print_success(f"All requests successful (avg {avg_time*1000:.0f}ms)")
            self.test_results.append(
                ("Connection Stability", True, f"{success_count}/10 succeeded")
            )
            return True
        else:
            self.print_error(f"Failed {failure_count}/10 requests")
            self.test_results.append(
                ("Connection Stability", False, f"{failure_count}/10 failed")
            )
            return False

    def print_summary(self):
        """Print test results summary."""
        self.print_header("TEST RESULTS SUMMARY")

        passed = sum(1 for _, result, _ in self.test_results if result)
        failed = sum(1 for _, result, _ in self.test_results if not result)
        total = len(self.test_results)

        print(f"\nTotal Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")

        print("\nDetailed Results:")
        print(f"{'-' * 60}")

        for test_name, result, details in self.test_results:
            status_icon = "✓" if result else "✗"
            status_color = Colors.GREEN if result else Colors.RED
            print(f"{status_color}{status_icon} {test_name:30} {details}{Colors.RESET}")

        print(f"{'-' * 60}")

        if failed == 0:
            self.print_success(
                "\n🎉 ALL TESTS PASSED - Database connection fix is working!"
            )
        else:
            self.print_error(
                f"\n❌ {failed} TEST(S) FAILED - Database connection issue may persist"
            )

        if self.start_time:
            elapsed = time.time() - self.start_time
            print(f"\nTotal test duration: {elapsed:.2f}s")

    def run_all_tests(self):
        """Run all tests in sequence."""
        self.start_time = time.time()

        print(f"\n{Colors.BOLD}Database Connection Validation Test Suite{Colors.RESET}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Base URL: {self.base_url}")

        # Test 1: Server reachability
        server_ok = self.test_api_server_reachable()
        if not server_ok:
            self.print_error("\n⚠ API server not reachable. Stopping tests.")
            self.print_info("Start the server with: docker-compose up")
            self.print_summary()
            return False

        # Test 2: Health check
        health_ok = self.test_health_check()

        # Test 3: API status
        self.test_api_status()

        # Test 4: User registration (only if health check passed)
        if health_ok:
            test_email, test_password = self.test_user_registration()

            # Test 5: User login (only if registration worked)

            self.test_user_login(test_email, test_password)

            # Test 6: Connection stability
            self.test_connection_stability()
        else:
            self.print_warning(
                "\nSkipping registration/login tests due to database connection failure"
            )

        # Print summary
        self.print_summary()

        # Return overall result
        failed = sum(1 for _, result, _ in self.test_results if not result)
        return failed == 0


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="API endpoint testing for database connection validation"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API server (default: http://localhost:8000)",
    )
    args = parser.parse_args()

    tester = APITester(base_url=args.url)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
