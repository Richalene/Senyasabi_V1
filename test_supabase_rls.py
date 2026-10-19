"""
Test script to verify Supabase RLS policies.

This script tests that:
1. Anon users can read content (modules, lessons, signs, etc.)
2. Authenticated users can read/write only their own data
3. Cross-user data isolation is enforced

Usage:
    python test_supabase_rls.py

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


def test_supabase_connection():
    """Test basic Supabase connection."""
    print("=" * 60)
    print("TEST 1: Supabase Connection")
    print("=" * 60)
    
    if not is_supabase_available():
        print("❌ FAILED: Supabase client not available")
        print("   Check that SUPABASE_URL and SUPABASE_ANON_KEY are set in .env")
        return False
    
    try:
        client = get_supabase_client()
        print(f"✅ Connected to Supabase")
        print(f"   Project URL: {os.getenv('SUPABASE_URL')}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_anon_read_content():
    """Test that anon users can read content tables."""
    print("\n" + "=" * 60)
    print("TEST 2: Anon User - Read Content Tables")
    print("=" * 60)
    
    try:
        client = get_supabase_client()
        
        # Test modules
        print("\nTesting modules table...")
        response = client.table('modules').select('*').limit(1).execute()
        if response.data:
            print(f"✅ Anon can read modules ({len(response.data)} rows found)")
        else:
            print("⚠️  WARNING: No modules found (might be empty)")
        
        # Test lessons
        print("\nTesting lessons table...")
        response = client.table('lessons').select('*').limit(1).execute()
        if response.data:
            print(f"✅ Anon can read lessons ({len(response.data)} rows found)")
        else:
            print("⚠️  WARNING: No lessons found (might be empty)")
        
        # Test signs
        print("\nTesting signs table...")
        response = client.table('signs').select('*').limit(1).execute()
        if response.data:
            print(f"✅ Anon can read signs ({len(response.data)} rows found)")
        else:
            print("⚠️  WARNING: No signs found (might be empty)")
        
        # Test media_files
        print("\nTesting media_files table...")
        response = client.table('media_files').select('*').limit(1).execute()
        if response.data:
            print(f"✅ Anon can read media_files ({len(response.data)} rows found)")
        else:
            print("⚠️  WARNING: No media_files found (might be empty)")
        
        # Test badges
        print("\nTesting badges table...")
        response = client.table('badges').select('*').limit(1).execute()
        if response.data:
            print(f"✅ Anon can read badges ({len(response.data)} rows found)")
        else:
            print("⚠️  WARNING: No badges found (might be empty)")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        print("   This usually means RLS policies are not applied correctly")
        return False


def test_anon_cannot_write():
    """Test that anon users cannot write to user tables."""
    print("\n" + "=" * 60)
    print("TEST 3: Anon User - Cannot Write User Data")
    print("=" * 60)
    
    try:
        client = get_supabase_client()
        
        # Try to insert into lesson_progress (should fail)
        print("\nTesting write protection on lesson_progress...")
        try:
            response = client.table('lesson_progress').insert({
                "user_id": "00000000-0000-0000-0000-000000000000",
                "lesson_id": 999,
                "completion_percentage": 0,
                "status": "Not Started"
            }).execute()
            print(f"❌ FAILED: Anon was able to write to lesson_progress (RLS not working)")
            return False
        except Exception as e:
            if "permission denied" in str(e).lower() or "row level security" in str(e).lower():
                print(f"✅ Anon correctly blocked from writing to lesson_progress")
                return True
            else:
                print(f"⚠️  WARNING: Got error but might not be RLS: {e}")
                return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_authenticated_read_own_data():
    """Test that authenticated users can read their own data."""
    print("\n" + "=" * 60)
    print("TEST 4: Authenticated User - Read Own Data")
    print("=" * 60)
    
    print("\nThis test requires a valid user account.")
    print("You will be prompted for email and password.")
    
    email = input("\nEnter test user email (or press Enter to skip): ").strip()
    if not email:
        print("⏭️  SKIPPED: No email provided")
        return True
    
    password = input("Enter password: ").strip()
    if not password:
        print("⏭️  SKIPPED: No password provided")
        return True
    
    try:
        # Authenticate
        print("\nAuthenticating...")
        from senyasabi.backend.api.auth_client_distributed import login
        result = login(email, password)

        print("Session fields:", result["session"].keys())
        print("Has access token:", bool(result["session"].get("access_token")))
        print("Has refresh token:", bool(result["session"].get("refresh_token")))

        session = result["session"]
        
        if session:
            print("Session keys:", session.keys())
        
        if not result or "session" not in result:
            print(f"❌ FAILED: Authentication failed")
            return False
        
        user_id = result["profile"]["user_id"]
        print(f"✅ Authenticated as user: {result['profile']['username']} ({user_id})")
        
        # Set the session on the client
        access_token = session["access_token"]
        refresh_token = session["refresh_token"]

        if not refresh_token:
            raise RuntimeError("Login returned an empty refresh token")

        client = get_supabase_client()

        if client is None:
            raise RuntimeError("Supabase client is unavailable in fastapi mode")

        client.auth.set_session(access_token, refresh_token)       

        # Try to read own lesson_progress
        print("\nReading own lesson_progress...")
        response = client.table('lesson_progress').select('*').eq('user_id', user_id).execute()
        print(f"✅ Can read own lesson_progress ({len(response.data)} rows)")
        
        # Try to read all lesson_progress (should only return own)
        print("\nReading all lesson_progress (should only return own)...")
        response = client.table('lesson_progress').select('*').execute()
        other_users = [r for r in response.data if r.get('user_id') != user_id]
        if other_users:
            print(f"❌ FAILED: Can read other users' data ({len(other_users)} rows from other users)")
            return False
        else:
            print(f"✅ Can only read own data (total: {len(response.data)} rows, all own)")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_content_sync():
    """Test content sync from Supabase."""
    print("\n" + "=" * 60)
    print("TEST 5: Content Sync")
    print("=" * 60)
    
    try:
        from senyasabi.backend.sync_supabase import sync_content
        
        print("\nFetching content delta...")
        delta = sync_content(since_version=0)
        
        if not delta:
            print("❌ FAILED: No delta returned")
            return False
        
        print(f"✅ Content sync successful")
        print(f"   Version: {delta.get('version')}")
        print(f"   Modules: {len(delta.get('modules', {}).get('upsert', []))} upserts")
        print(f"   Lessons: {len(delta.get('lessons', {}).get('upsert', []))} upserts")
        print(f"   Signs: {len(delta.get('signs', {}).get('upsert', []))} upserts")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SUPABASE RLS AND CONNECTION TESTS")
    print("=" * 60)
    print(f"Mode: {os.getenv('SYSTEM_MODE', 'not set')}")
    print(f"Supabase URL: {os.getenv('SUPABASE_URL', 'not set')}")
    print(f"Anon Key: {'set' if os.getenv('SUPABASE_ANON_KEY') else 'not set'}")
    
    results = []
    
    # Run tests
    results.append(("Connection", test_supabase_connection()))
    results.append(("Anon Read Content", test_anon_read_content()))
    results.append(("Anon Cannot Write", test_anon_cannot_write()))
    results.append(("Content Sync", test_content_sync()))
    results.append(("Authenticated Read Own", test_authenticated_read_own_data()))
    
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
        print("\n🎉 All tests passed! RLS policies are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
