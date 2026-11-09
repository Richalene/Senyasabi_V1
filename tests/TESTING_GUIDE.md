# Supabase Integration Testing Guide

## Overview

Three test scripts are provided to verify Supabase integration in distributed mode:

1. **test_supabase_rls.py** - Tests RLS policies and data isolation
2. **test_supabase_auth.py** - Tests authentication operations
3. **test_supabase_sync.py** - Tests sync operations
4. **test_all_supabase.py** - Master runner for all tests

## Prerequisites

Before running tests, ensure:

1. **Environment is configured:**
   ```bash
   cp .env.dist .env
   # Edit .env with your Supabase credentials
   # Required: SUPABASE_URL, SUPABASE_ANON_KEY
   # Required: SYSTEM_MODE=distributed
   ```

2. **RLS policies are applied to database:**
   - Run `senyasabi/backend/database/migrations/001_add_rls_policies.sql` in Supabase SQL Editor
   - See DISTRIBUTED_CLIENT_README.md for details

3. **Test user account exists** (for authenticated tests):
   - You can create one via the registration test
   - Or use an existing account

## Running Tests

### Option 1: Run All Tests (Recommended)

```bash
python test_all_supabase.py
```

This will run all test suites in sequence.

### Option 2: Run Individual Tests

#### Test RLS Policies
```bash
python test_supabase_rls.py
```

Tests:
- ✅ Supabase connection
- ✅ Anon users can read content
- ✅ Anon users cannot write user data
- ✅ Authenticated users can read own data only
- ✅ Content sync works

#### Test Authentication
```bash
python test_supabase_auth.py
```

Tests:
- ✅ Supabase connection
- ✅ User registration
- ✅ User login
- ✅ Token refresh
- ✅ Username lookup
- ✅ Email lookup

**Interactive:** Requires email/password input for login tests.

#### Test Sync Operations
```bash
python test_supabase_sync.py
```

Tests:
- ✅ Supabase connection
- ✅ Content sync
- ✅ Progress upload
- ✅ Quiz attempt upload
- ✅ Incremental sync

**Interactive:** Requires email/password for upload tests.

## Expected Output

### Successful Test Run

```
======================================================================
SUPABASE RLS AND CONNECTION TESTS
======================================================================
Mode: distributed
Supabase URL: https://your-project.supabase.co
Anon Key: set
============================================================
TEST 1: Supabase Connection
============================================================
✅ Connected to Supabase
   Project URL: https://your-project.supabase.co

...

======================================================================
TEST SUMMARY
======================================================================
✅ PASS: Connection
✅ PASS: Anon Read Content
✅ PASS: Anon Cannot Write
✅ PASS: Content Sync
✅ PASS: Authenticated Read Own

Total: 5/5 tests passed

🎉 All tests passed! RLS policies are working correctly.
```

### Common Issues and Solutions

#### Issue: "Supabase client not available"

**Cause:** `SUPABASE_URL` or `SUPABASE_ANON_KEY` not set in `.env`

**Solution:**
```bash
# Check .env file
cat .env

# Should have:
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_ANON_KEY=your-anon-key
# SYSTEM_MODE=distributed
```

#### Issue: "permission denied" or RLS errors

**Cause:** RLS policies not applied to database

**Solution:**
1. Open Supabase Dashboard → SQL Editor
2. Run contents of `senyasabi/backend/database/migrations/001_add_rls_policies.sql`
3. Verify policies are applied:
```sql
SELECT schemaname, tablename, policyname 
FROM pg_policies 
WHERE schemaname = 'public';
```

#### Issue: Authentication fails

**Cause:** Invalid credentials or email not confirmed

**Solution:**
- Verify email and password are correct
- Check if email confirmation is required (Supabase Auth setting)
- Try registering a new test user via the test script

#### Issue: "No modules/lessons found"

**Cause:** Database is empty (no content seeded)

**Solution:**
- This is expected for a fresh database
- Content sync will return empty results
- This is not a failure - RLS is still working correctly

## Test Details

### test_supabase_rls.py

**Purpose:** Verify RLS policies enforce data isolation

**Tests:**
1. **Connection** - Basic Supabase connectivity
2. **Anon Read Content** - Anon can read content tables (modules, lessons, signs, media, badges)
3. **Anon Cannot Write** - Anon blocked from writing to user tables
4. **Content Sync** - Content delta fetch works
5. **Authenticated Read Own** - Authenticated users can only read their own data

**Interactive:** Requires email/password for authenticated test

### test_supabase_auth.py

**Purpose:** Verify Supabase Auth integration

**Tests:**
1. **Connection** - Basic Supabase connectivity
2. **Registration** - User registration via Supabase Auth
3. **Login** - User login with email/password
4. **Token Refresh** - Access token refresh
5. **Username Lookup** - Username-to-email resolution
6. **Email Lookup** - Email-to-user resolution

**Interactive:** Requires input for registration, login, and lookups

### test_supabase_sync.py

**Purpose:** Verify sync operations with Supabase

**Tests:**
1. **Connection** - Basic Supabase connectivity
2. **Content Sync** - Fetch content delta from Supabase
3. **Progress Upload** - Upload lesson progress to Supabase
4. **Quiz Attempt Upload** - Upload quiz attempt to Supabase
5. **Incremental Sync** - Sync with version filtering

**Interactive:** Requires email/password for upload tests

## Continuous Integration

For CI/CD pipelines, you can run non-interactive tests:

```bash
# Run RLS tests (no auth required)
python test_supabase_rls.py

# Run content sync test (no auth required)
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
os.environ['SYSTEM_MODE'] = 'distributed'
from senyasabi.backend.sync_supabase import sync_content
delta = sync_content(0)
print(f'Content sync: {\"PASS\" if delta else \"FAIL\"}')"
"
```

## Troubleshooting

### Enable Debug Logging

Add this to your test script or `.env`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Supabase Dashboard

While tests run, monitor:
- **Dashboard → Database → Logs** - See SQL queries
- **Dashboard → Auth → Users** - See created users
- **Dashboard → Database → Table Editor** - Verify data

### Test with Different Credentials

Create a dedicated test user:
```bash
# Use test_auth.py to register
python test_supabase_auth.py
# Follow prompts to register test_user@example.com
```

## Post-Test Validation

After tests pass, verify in Supabase Dashboard:

1. **Check users:**
   - Dashboard → Auth → Users
   - Should see test user if registration test ran

2. **Check lesson_progress:**
   - Dashboard → Database → Table Editor → lesson_progress
   - Should see progress if upload test ran

3. **Check RLS policies:**
   - Dashboard → Database → Policies
   - Should see policies for all tables

## Next Steps After Testing

Once all tests pass:

1. ✅ Apply RLS policies to production database
2. ✅ Build distributed client: `python build_distributed.py`
3. ✅ Test built executable on clean machine
4. ✅ Verify no sensitive keys in build
5. ✅ Deploy to distribution channel

## Support

If tests fail:
1. Check this guide's troubleshooting section
2. Review test output for specific error messages
3. Verify Supabase Dashboard configuration
4. Check DATABASE_URL is NOT set (should be None in distributed mode)
