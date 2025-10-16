#!/usr/bin/env python3
"""
Debug script for Supabase signup error.
This script will test the Supabase signup API directly to identify the issue.
"""

import os
import sys
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_supabase_connection():
    """Test basic Supabase connection."""
    print("🔍 Testing Supabase Connection...")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_anon_key:
        print("❌ Missing Supabase configuration!")
        print(f"SUPABASE_URL: {'✅' if supabase_url else '❌'}")
        print(f"SUPABASE_ANON_KEY: {'✅' if supabase_anon_key else '❌'}")
        return None

    print(f"✅ Supabase URL: {supabase_url}")
    print(f"✅ Anon Key: {supabase_anon_key[:20]}...")

    try:
        supabase: Client = create_client(supabase_url, supabase_anon_key)
        print("✅ Supabase client created successfully")
        return supabase
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        return None


def test_signup(supabase: Client, email: str, password: str):
    """Test user signup with detailed error reporting."""
    print(f"\n🔍 Testing signup for: {email}")

    try:
        # Attempt signup
        auth_response = supabase.auth.sign_up({"email": email, "password": password})

        print("✅ Signup response received")
        print(f"Response type: {type(auth_response)}")
        print(f"Response: {auth_response}")

        if hasattr(auth_response, "user"):
            print(f"User: {auth_response.user}")
        if hasattr(auth_response, "session"):
            print(f"Session: {auth_response.session}")

        return auth_response

    except Exception as e:
        print(f"❌ Signup failed with error: {e}")
        print(f"Error type: {type(e)}")

        # Try to get more detailed error information
        if hasattr(e, "response"):
            print(f"Response object: {e.response}")
        if hasattr(e, "status_code"):
            print(f"Status code: {e.status_code}")
        if hasattr(e, "message"):
            print(f"Message: {e.message}")

        return None


def test_signup_with_manual_request():
    """Test signup using manual HTTP request to see raw response."""
    import requests

    print("\n🔍 Testing signup with manual HTTP request...")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")

    url = f"{supabase_url}/auth/v1/signup"
    headers = {"apikey": supabase_anon_key, "Content-Type": "application/json"}
    data = {"email": "test@doWhat.com", "password": "TestPassword123!"}

    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")

        if response.status_code != 200:
            try:
                error_data = response.json()
                print(f"Error JSON: {json.dumps(error_data, indent=2)}")
            except:
                print("Could not parse error response as JSON")

        return response

    except Exception as e:
        print(f"❌ Manual request failed: {e}")
        return None


def main():
    """Main debug function."""
    print("🚀 Supabase Signup Debug Tool")
    print("=" * 50)

    # Test 1: Basic connection
    supabase = test_supabase_connection()
    if not supabase:
        print("\n❌ Cannot proceed without Supabase connection")
        return

    # Test 2: Manual HTTP request to see raw response
    print("\n" + "=" * 50)
    manual_response = test_signup_with_manual_request()

    # Test 3: Using Supabase client
    print("\n" + "=" * 50)
    test_signup(supabase, "test@example.com", "TestPassword123!")

    print("\n" + "=" * 50)
    print("🏁 Debug complete!")


if __name__ == "__main__":
    main()
