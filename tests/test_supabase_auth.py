"""
Test script to verify Supabase Auth integration.

This script tests:
1. User registration with Supabase Auth
2. User login with Supabase Auth
3. Token refresh
4. Username-to-email lookup

Usage:
    python test_supabase_auth.py

Requirements:
    - SUPABASE_URL and SUPABASE_ANON_KEY in .env
    - SYSTEM_MODE=distributed in .env
"""
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Set distributed mode for testing
os.environ["SYSTEM_MODE"] = "distributed"

from senyasabi.backend.supabase_client import get_supabase_client, is_supabase_available
from senyasabi.backend.api.auth_client_distributed import (
    register,
    login,
    refresh,
    get_user_by_email,
    get_user_by_username,
    AuthError,
    NetworkError
)


def test_connection():
    """Test basic Supabase connection."""
    print("=" * 60)
    print("TEST 1: Supabase Connection")
    print("=" * 60)
    
    if not is_supabase_available():
        print("❌ FAILED: Supabase client not available")
        return False
    
    try:
        client = get_supabase_client()
        print(f"✅ Connected to Supabase")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_registration():
    """Test user registration."""
    print("\n" + "=" * 60)
    print("TEST 2: User Registration")
    print("=" * 60)
    
    print("\nNOTE: This will create a test user account.")
    print("Use a unique email to avoid conflicts.")
    
    username = input("\nEnter test username (or press Enter to skip): ").strip()
    if not username:
        print("⏭️  SKIPPED")
        return True
    
    email = input("Enter test email: ").strip()
    if not email:
        print("❌ FAILED: Email required")
        return False
    
    password = input("Enter test password (min 8 chars): ").strip()
    if len(password) < 8:
        print("❌ FAILED: Password must be at least 8 characters")
        return False
    
    display_name = input("Enter display name (optional): ").strip() or username
    
    try:
        print("\nRegistering user...")
        result = register(username, email, password, display_name)
        
        print(f"✅ Registration successful")
        print(f"   Username: {result['username']}")
        print(f"   Email: {result['email']}")
        print(f"   Display Name: {result['display_name']}")
        print(f"   Email Confirmation Required: {result['needs_confirmation']}")
        
        if result['needs_confirmation']:
            print("\n⚠️  WARNING: Email confirmation is required")
            print("   You'll need to confirm the email before logging in")
        
        return True
        
    except AuthError as e:
        print(f"❌ FAILED (AuthError): {e}")
        return False
    except NetworkError as e:
        print(f"❌ FAILED (NetworkError): {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_login():
    """Test user login."""
    print("\n" + "=" * 60)
    print("TEST 3: User Login")
    print("=" * 60)
    
    email = input("\nEnter email (or press Enter to skip): ").strip()
    if not email:
        print("⏭️  SKIPPED")
        return True
    
    password = input("Enter password: ").strip()
    if not password:
        print("❌ FAILED: Password required")
        return False
    
    try:
        print("\nLogging in...")
        result = login(email, password)
        
        print(f"✅ Login successful")
        print(f"   User ID: {result['profile']['user_id']}")
        print(f"   Username: {result['profile']['username']}")
        print(f"   Email: {result['profile']['email']}")
        print(f"   Display Name: {result['profile']['display_name']}")
        print(f"   Access Token: {result['session']['access_token'][:20]}...")
        print(f"   Refresh Token: {result['session']['refresh_token'][:20]}...")
        print(f"   Expires At: {result['session']['expires_at']}")
        
        # Save refresh token for refresh test
        global _test_refresh_token
        _test_refresh_token = result['session']['refresh_token']
        
        return True
        
    except AuthError as e:
        print(f"❌ FAILED (AuthError): {e}")
        return False
    except NetworkError as e:
        print(f"❌ FAILED (NetworkError): {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


_test_refresh_token = None


def test_token_refresh():
    """Test token refresh."""
    print("\n" + "=" * 60)
    print("TEST 4: Token Refresh")
    print("=" * 60)
    
    if not _test_refresh_token:
        print("⏭️  SKIPPED: No refresh token available (run login test first)")
        return True
    
    try:
        print("\nRefreshing token...")
        result = refresh(_test_refresh_token)
        
        print(f"✅ Token refresh successful")
        print(f"   New Access Token: {result['session']['access_token'][:20]}...")
        print(f"   New Refresh Token: {result['session']['refresh_token'][:20]}...")
        print(f"   New Expires At: {result['session']['expires_at']}")
        
        return True
        
    except AuthError as e:
        print(f"❌ FAILED (AuthError): {e}")
        return False
    except NetworkError as e:
        print(f"❌ FAILED (NetworkError): {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_username_lookup():
    """Test username-to-email lookup."""
    print("\n" + "=" * 60)
    print("TEST 5: Username Lookup")
    print("=" * 60)
    
    username = input("\nEnter username to look up (or press Enter to skip): ").strip()
    if not username:
        print("⏭️  SKIPPED")
        return True
    
    try:
        print(f"\nLooking up username: {username}")
        user = get_user_by_username(username)
        
        if user:
            print(f"✅ Username found")
            print(f"   User ID: {user['user_id']}")
            print(f"   Username: {user['username']}")
            print(f"   Email: {user['email']}")
            print(f"   Display Name: {user['display_name']}")
            return True
        else:
            print(f"⚠️  WARNING: Username not found (might not exist or RLS blocks access)")
            return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_email_lookup():
    """Test email lookup."""
    print("\n" + "=" * 60)
    print("TEST 6: Email Lookup")
    print("=" * 60)
    
    email = input("\nEnter email to look up (or press Enter to skip): ").strip()
    if not email:
        print("⏭️  SKIPPED")
        return True
    
    try:
        print(f"\nLooking up email: {email}")
        user = get_user_by_email(email)
        
        if user:
            print(f"✅ Email found")
            print(f"   User ID: {user['user_id']}")
            print(f"   Username: {user['username']}")
            print(f"   Email: {user['email']}")
            print(f"   Display Name: {user['display_name']}")
            return True
        else:
            print(f"⚠️  WARNING: Email not found (might not exist or RLS blocks access)")
            return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SUPABASE AUTH INTEGRATION TESTS")
    print("=" * 60)
    print(f"Mode: {os.getenv('SYSTEM_MODE', 'not set')}")
    print(f"Supabase URL: {os.getenv('SUPABASE_URL', 'not set')}")
    
    results = []
    
    # Run tests
    results.append(("Connection", test_connection()))
    results.append(("Registration", test_registration()))
    results.append(("Login", test_login()))
    results.append(("Token Refresh", test_token_refresh()))
    results.append(("Username Lookup", test_username_lookup()))
    results.append(("Email Lookup", test_email_lookup()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Supabase Auth integration is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
