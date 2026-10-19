"""
Master test runner for all Supabase integration tests.

This script runs all test scripts in sequence:
1. test_supabase_rls.py - RLS policies and data isolation
2. test_supabase_auth.py - Authentication operations
3. test_supabase_sync.py - Sync operations

Usage:
    python test_all_supabase.py

Requirements:
    - SUPABASE_URL and SUPABASE_ANON_KEY in .env
    - SENYESABI_MODE=distributed in .env
    - Python 3.8+
"""
import sys
import subprocess
from pathlib import Path


def run_test(script_name, description):
    """Run a test script and return success status."""
    print("\n" + "=" * 70)
    print(f"RUNNING: {description}")
    print("=" * 70)
    
    script_path = Path(script_name)
    if not script_path.exists():
        print(f"❌ ERROR: Test script not found: {script_name}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ ERROR running test: {e}")
        return False


def main():
    """Run all tests and report results."""
    print("\n" + "=" * 70)
    print("SUPABASE INTEGRATION TEST SUITE")
    print("=" * 70)
    print("\nThis will run all Supabase integration tests in sequence.")
    print("Some tests require interactive input (user credentials).")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    input()
    
    tests = [
        ("test_supabase_rls.py", "RLS Policies and Data Isolation"),
        ("test_supabase_auth.py", "Authentication Operations"),
        ("test_supabase_sync.py", "Sync Operations"),
    ]
    
    results = []
    
    for script, description in tests:
        success = run_test(script, description)
        results.append((description, success))
    
    # Final summary
    print("\n" + "=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {description}")
    
    print(f"\nTotal: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 All test suites passed!")
        print("\nYour Supabase integration is ready for production use.")
        print("\nNext steps:")
        print("1. Apply RLS policies to production database")
        print("2. Build distributed client: python build_distributed.py")
        print("3. Test the built executable on a clean machine")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed.")
        print("\nReview the output above and fix any issues before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
