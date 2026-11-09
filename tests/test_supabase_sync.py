"""
Test script to verify Supabase sync operations.

This script tests:
1. Content sync from Supabase
2. Progress upload to Supabase
3. Sync queue processing

Usage:
    python test_supabase_sync.py

Requirements:
    - SUPABASE_URL and SUPABASE_ANON_KEY in .env
    - SYSTEM_MODE=distributed in .env
    - Valid user credentials for authenticated tests
"""
import os
import sys
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Set distributed mode for testing
os.environ["SYSTEM_MODE"] = "distributed"

from senyasabi.backend.supabase_client import get_supabase_client, is_supabase_available
from senyasabi.backend.sync_supabase import sync_content, upload_sync


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


def test_content_sync():
    """Test content sync from Supabase."""
    print("\n" + "=" * 60)
    print("TEST 2: Content Sync")
    print("=" * 60)
    
    try:
        print("\nFetching content delta (since version 0)...")
        delta = sync_content(since_version=0)
        
        if not delta:
            print("❌ FAILED: No delta returned")
            return False
        
        print(f"✅ Content sync successful")
        print(f"   Version: {delta.get('version')}")
        print(f"   Since Version: {delta.get('since_version')}")
        
        # Count rows in each table
        for table in ['modules', 'lessons', 'signs', 'media_files', 'quizzes', 'minigames', 'badges']:
            table_data = delta.get(table, {})
            if isinstance(table_data, dict):
                upserts = len(table_data.get('upsert', []))
                deletes = len(table_data.get('delete', []))
            else:
                # Handle case where it might be a list (legacy)
                upserts = len(table_data) if isinstance(table_data, list) else 0
                deletes = 0
            print(f"   {table}: {upserts} upserts, {deletes} deletes")
        
        # Validate structure
        required_keys = ['version', 'modules', 'lessons', 'signs']
        missing = [k for k in required_keys if k not in delta]
        if missing:
            print(f"❌ FAILED: Missing required keys: {missing}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_progress_upload():
    """Test progress upload to Supabase."""
    print("\n" + "=" * 60)
    print("TEST 3: Progress Upload")
    print("=" * 60)
    
    print("\nThis test requires authenticated access.")
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
        
        if not result or "session" not in result:
            print(f"❌ FAILED: Authentication failed")
            return False
        
        user_id = result["profile"]["user_id"]
        print(f"✅ Authenticated as user: {result['profile']['username']} ({user_id})")
        
        # Set the session on the client (requires both access_token and refresh_token)
        access_token = result["session"]["access_token"]
        refresh_token = result["session"]["refresh_token"]
        client = get_supabase_client()
        client.auth.set_session(access_token, refresh_token)
        
        # Test lesson progress upload
        print("\nUploading lesson progress...")
        sync_items = [{
            "entity_type": "lesson_progress",
            "client_id": str(uuid.uuid4()),
            "data": {
                "lesson_id": 1,  # Use a real lesson_id in production
                "completion_percentage": 50.0,
                "status": "In Progress",
                "time_spent_seconds": 300,
                "client_updated_at": datetime.now(timezone.utc).isoformat()
            },
            "operation": "upsert"
        }]
        
        upload_result = upload_sync(str(user_id), sync_items)
        
        if upload_result:
            print(f"✅ Progress upload successful")
            print(f"   Processed: {upload_result.get('processed')}")
            print(f"   Succeeded: {upload_result.get('succeeded')}")
            print(f"   Failed: {upload_result.get('failed')}")
            return True
        else:
            print("❌ FAILED: Upload returned None")
            return False
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quiz_attempt_upload():
    """Test quiz attempt upload to Supabase."""
    print("\n" + "=" * 60)
    print("TEST 4: Quiz Attempt Upload")
    print("=" * 60)
    
    print("\nThis test requires authenticated access.")
    print("Use the same credentials as test 3 if you want to skip re-entering.")
    
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
        
        if not result or "session" not in result:
            print(f"❌ FAILED: Authentication failed")
            return False
        
        user_id = result["profile"]["user_id"]
        print(f"✅ Authenticated as user: {result['profile']['username']} ({user_id})")
        
        # Set the session on the client (requires both access_token and refresh_token)
        access_token = result["session"]["access_token"]
        refresh_token = result["session"]["refresh_token"]
        
        client = get_supabase_client()
        client.auth.set_session(access_token, refresh_token)
        
        # Test quiz attempt upload
        print("\nUploading quiz attempt...")
        sync_items = [{
            "entity_type": "quiz_attempt",
            "client_id": str(uuid.uuid4()),
            "data": {
                "attempt_id": str(uuid.uuid4()),  # Required primary key
                "quiz_id": 1,  # Use a real quiz_id in production
                "started_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "score": 85,
                "max_score": 100
            },
            "operation": "upsert"
        }]
        
        upload_result = upload_sync(str(user_id), sync_items)
        
        if upload_result:
            print(f"✅ Quiz attempt upload successful")
            print(f"   Processed: {upload_result.get('processed')}")
            print(f"   Succeeded: {upload_result.get('succeeded')}")
            print(f"   Failed: {upload_result.get('failed')}")
            return True
        else:
            print("❌ FAILED: Upload returned None")
            return False
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_incremental_sync():
    """Test incremental content sync."""
    print("\n" + "=" * 60)
    print("TEST 5: Incremental Content Sync")
    print("=" * 60)
    
    try:
        # First sync
        print("\nFirst sync (since version 0)...")
        delta1 = sync_content(since_version=0)
        version1 = delta1.get('version') if delta1 else 0
        print(f"   Current version: {version1}")
        
        # Second sync (should return no changes)
        print("\nSecond sync (since version {version1})...")
        delta2 = sync_content(since_version=version1)
        
        if delta2:
            version2 = delta2.get('version')
            if version2 == version1:
                print(f"✅ Incremental sync working (no new changes)")
                return True
            else:
                print(f"⚠️  WARNING: Version changed unexpectedly ({version1} -> {version2})")
                return True
        else:
            print("❌ FAILED: Second sync returned None")
            return False
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SUPABASE SYNC OPERATIONS TESTS")
    print("=" * 60)
    print(f"Mode: {os.getenv('SYSTEM_MODE', 'not set')}")
    print(f"Supabase URL: {os.getenv('SUPABASE_URL', 'not set')}")
    
    results = []
    
    # Run tests
    results.append(("Connection", test_connection()))
    results.append(("Content Sync", test_content_sync()))
    results.append(("Progress Upload", test_progress_upload()))
    results.append(("Quiz Attempt Upload", test_quiz_attempt_upload()))
    results.append(("Incremental Sync", test_incremental_sync()))
    
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
        print("\n🎉 All tests passed! Supabase sync operations are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
