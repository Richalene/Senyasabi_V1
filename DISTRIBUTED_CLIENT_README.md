# Distributed Client Implementation

## Overview

The SenyaSabi desktop client now supports two modes:
- **FastAPI Mode** (default): Client → FastAPI backend → Supabase
- **Distributed Mode**: Client → Supabase (direct anon access)

This allows distribution without sensitive API keys while maintaining security through Supabase's Row Level Security (RLS).

## What Was Implemented

### 1. PostgreSQL RLS Policies
**File:** `senyasabi/backend/database/migrations/001_add_rls_policies.sql`

Created comprehensive RLS policies that:
- Allow anon users to read content (modules, lessons, signs, media, quizzes, minigames, badges)
- Allow authenticated users to read/write only their own data (progress, attempts, badges, streaks, statistics)
- Enforce data isolation at the database level

**To apply:** Run this SQL script in your Supabase SQL editor:
```bash
psql -f senyasabi/backend/database/migrations/001_add_rls_policies.sql
```

### 2. Supabase Client Factory
**File:** `senyasabi/backend/supabase_client.py`

Created a Supabase client factory that:
- Provides direct Supabase access in distributed mode
- Returns None in fastapi mode (for backward compatibility)
- Handles lazy initialization and error checking

### 3. Dual-Mode Configuration
**File:** `senyasabi/backend/config.py`

Added `CLIENT_MODE` environment variable:
- `SENYESABI_MODE=fastapi` (default): Uses FastAPI proxy
- `SENYESABI_MODE=distributed`: Uses direct Supabase access

Secret keys (DATABASE_URL, SUPABASE_SERVICE_ROLE_KEY) are automatically disabled in distributed mode.

### 4. Distributed Auth Client
**File:** `senyasabi/backend/api/auth_client_distributed.py`

Created direct Supabase Auth integration:
- Registration via Supabase Auth
- Login via Supabase Auth
- Token refresh via Supabase Auth
- Username-to-email lookup for login

### 5. Auth Service Integration
**File:** `senyasabi/backend/auth_service.py`

Updated to use appropriate auth client based on mode:
- FastAPI mode: Uses `auth_client` (FastAPI proxy)
- Distributed mode: Uses `auth_client_distributed` (direct Supabase)
- Offline auth logic unchanged (still uses SQLite + argon2)

### 6. Sync Service Update
**File:** `senyasabi/backend/sync_service.py` + `senyasabi/backend/sync_supabase.py`

Created Supabase sync operations:
- `sync_supabase.py`: Direct Supabase queries for content sync and progress upload
- `sync_service.py`: Mode-aware routing to appropriate sync method

### 7. API Client Update
**File:** `senyasabi/backend/api_client.py`

Updated to use Supabase in distributed mode:
- `sync_content()`: Uses Supabase queries in distributed mode
- `upload_sync()`: Uses Supabase upserts in distributed mode
- All other methods unchanged (not used in distributed mode)

### 8. Media Service Update
**File:** `senyasabi/backend/media_service.py`

Updated to use Supabase Storage in distributed mode:
- `_get_media_info_supabase()`: Gets media metadata and URL from Supabase
- Falls back to FastAPI presigned URLs in fastapi mode

### 9. Distribution Template
**File:** `.env.dist`

Created environment template for distribution:
- Contains only public credentials (SUPABASE_URL, SUPABASE_ANON_KEY)
- Documents which credentials are safe to bundle
- Includes SENYESABI_MODE=distributed setting

### 10. Build Script
**File:** `build_distributed.py`

Created build script for distributed client:
- Creates .env from .env.dist template
- Verifies environment configuration
- Builds with PyInstaller (excludes FastAPI-specific files)
- Instructions for distribution

### 11. Syntax Fix
**File:** `senyasabi/backend/scripts/verify_postgres_schema.py`

Fixed syntax error (trailing comma in list).

## How to Use

### Development (FastAPI Mode)
No changes needed - continue using the FastAPI backend as before:
```bash
# Start FastAPI backend
python -m senyasabi.backend.main

# Run desktop client
python senyasabi/main.py
```

### Distribution (Distributed Mode)

#### Step 1: Apply RLS Policies
Run the migration script in your Supabase SQL editor:
```sql
-- Copy and paste contents of:
-- senyasabi/backend/database/migrations/001_add_rls_policies.sql
```

#### Step 2: Configure Environment
```bash
# Copy the template
cp .env.dist .env

# Edit .env with your Supabase credentials
# Required:
#   SUPABASE_URL=https://your-project.supabase.co
#   SUPABASE_ANON_KEY=your-anon-key
#   SENYESABI_MODE=distributed
```

#### Step 3: Build Distribution
```bash
# Install PyInstaller if not already installed
pip install pyinstaller

# Run build script
python build_distributed.py
```

The build script will:
- Verify environment configuration
- Build a standalone executable with PyInstaller
- Include the .env file with public credentials only

#### Step 4: Test Distributed Build
```bash
# Run the built executable
./dist/SenyaSabi
```

## Security Considerations

### Safe to Bundle (Public)
✅ `SUPABASE_URL` - Public project URL
✅ `SUPABASE_ANON_KEY` - Designed to be public, RLS enforces security

### Never Bundle (Secret)
❌ `SUPABASE_SERVICE_ROLE_KEY` - Full database access
❌ `DATABASE_URL` - Direct PostgreSQL connection with admin rights
❌ `S3_SECRET_KEY` - Storage admin access
❌ `SUPABASE_JWT_SECRET` - Token signing secret

### RLS Protection
- **Content tables**: Anon can read, no one can write (content managed via admin scripts)
- **User tables**: Authenticated users can read/write only their own data
- **Cross-user isolation**: Enforced at database level via RLS policies

## Migration Path

The implementation uses **Option A (Dual-Mode)** as planned:
- Client checks `SENYESABI_MODE` environment variable
- Default behavior unchanged (fastapi mode)
- Set `SENYESABI_MODE=distributed` for production builds
- Allows gradual transition and easy rollback

## Testing Checklist

Before distributing:
- [ ] Apply RLS policies to production database
- [ ] Test anon user can read content (no auth required)
- [ ] Test authenticated user can read/write own data only
- [ ] Test cross-user data isolation
- [ ] Test registration with Supabase Auth
- [ ] Test login with Supabase Auth
- [ ] Test token refresh works
- [ ] Test offline fallback still works
- [ ] Test content sync from Supabase
- [ ] Test progress upload to Supabase
- [ ] Test media download from Supabase Storage
- [ ] Verify no sensitive keys in bundled files
- [ ] Test on clean machine

## Rollback Plan

If issues arise with distributed mode:
1. Set `SENYESABI_MODE=fastapi` in .env
2. Continue using FastAPI backend
3. Rebuild with FastAPI mode
4. No code changes required

## Next Steps

For full production deployment:
1. Implement proper signed URL generation for Supabase Storage (currently using public URLs)
2. Add comprehensive error handling for network failures
3. Implement client-side caching for content to reduce Supabase queries
4. Add telemetry/logging for distributed mode debugging
5. Consider adding a migration script to transition existing users
6. Test with real users in beta before full rollout

## File Changes Summary

### New Files
- `senyasabi/backend/supabase_client.py` - Supabase client factory
- `senyasabi/backend/api/auth_client_distributed.py` - Direct Supabase Auth
- `senyasabi/backend/sync_supabase.py` - Supabase sync operations
- `senyasabi/backend/database/migrations/001_add_rls_policies.sql` - RLS policies
- `.env.dist` - Distribution config template
- `build_distributed.py` - Build script
- `DISTRIBUTED_CLIENT_README.md` - This file

### Modified Files
- `senyasabi/backend/config.py` - Added CLIENT_MODE detection
- `senyasabi/backend/auth_service.py` - Mode-aware auth client selection
- `senyasabi/backend/sync_service.py` - Mode-aware sync routing
- `senyasabi/backend/api_client.py` - Mode-aware API calls
- `senyasabi/backend/media_service.py` - Mode-aware media access
- `senyasabi/backend/scripts/verify_postgres_schema.py` - Fixed syntax error

### Not Modified (Still Work in FastAPI Mode)
- `senyasabi/backend/main.py` - FastAPI application
- `senyasabi/backend/api/` - FastAPI endpoints
- All admin scripts (continue to use service_role)
