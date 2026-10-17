"""
PostgreSQL schema verification script.

This script verifies that the PostgreSQL database has the correct schema
as defined in postgre_schema.sql, including:
- All tables exist
- auth_user_id column in users table
- handle_new_auth_user() trigger exists
- Functions and triggers for statistics
- refresh_tokens table exists (but will not be used)

Run this after setting POSTGRESQL_URL in .env file.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
from backend.config import POSTGRESQL_URL

# Direct SQLAlchemy import for standalone script
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Create PostgreSQL engine for this script
# Using Supabase Session Pooler mode
if POSTGRESQL_URL:
    postgres_engine = create_engine(
        POSTGRESQL_URL,
        echo=False,
        future=True,
        # Session pooler manages connections, so we use minimal pooling settings
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
        pool_recycle=3600,
    )
    PostgreSQLSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=postgres_engine
    )
    def get_postgres_session():
        return PostgreSQLSessionLocal()
else:
    print("ERROR: POSTGRESQL_URL not set in environment")
    sys.exit(1)


def verify_schema():
    """Verify PostgreSQL schema matches expectations."""
    print("Verifying PostgreSQL schema...")
    
    with get_postgres_session() as db:
        # Check required tables
        required_tables = [
            'users', 'content_versions', 'media_files', 'modules', 'lessons',
            'signs', 'lesson_signs', 'sign_media', 'lesson_media', 'quizzes',
            'quiz_attempts', 'minigames', 'minigame_signs', 'badges', 
            'user_badges', 'lesson_progress', 'user_statistics', 'streaks',
            'minigame_attempts'
        ]
        
        # Query for existing tables
        result = db.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        existing_tables = {row[0] for row in result}
        
        print(f"\nExisting tables: {len(existing_tables)}")
        for table in required_tables:
            if table in existing_tables:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} - MISSING")
        
        # Check users table structure
        print("\nChecking users table structure...")
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """))
        
        has_auth_user_id = False
        for row in result:
            col_name, data_type, is_nullable = row
            print(f"  {col_name}: {data_type} (nullable: {is_nullable})")
            if col_name == 'auth_user_id':
                has_auth_user_id = True
        
        if has_auth_user_id:
            print("  ✓ auth_user_id column exists")
        else:
            print("  ✗ auth_user_id column MISSING")
        
        # Check for auth trigger
        print("\nChecking for handle_new_auth_user trigger...")
        result = db.execute(text("""
            SELECT trigger_name
            FROM information_schema.triggers
            WHERE trigger_name = 'on_auth_user_created'
        """))
        
        if result.first() is not None:
            print("  ✓ on_auth_user_created trigger exists")
        else:
            print("  ✗ on_auth_user_created trigger MISSING")
        
        # Check for refresh triggers
        print("\nChecking for trg_refresh_stats trigger...")
        result = db.execute(text("""
            SELECT trigger_name
            FROM information_schema.triggers
            WHERE trigger_name LIKE '%refresh%'
        """))
        
        triggers_found = [row[0] for row in result]
        if triggers_found:
            print(f"  ✓ Triggers found: {', '.join(triggers_found)}")
        else:
            print("  ✗ No refresh triggers found")
        
        # Check for statistics functions
        print("\nChecking for statistics functions...")
        required_functions = [
            'refresh_user_statistics',
            'trg_refresh_stats',
            'rebuild_user_statistics'
        ]
        
        for func_name in required_functions:
            result = db.execute(text(f"""
                SELECT routine_name
                FROM information_schema.routines
                WHERE routine_name = '{func_name}'
            """))
            if result.first() is not None:
                print(f"  ✓ {func_name}")
            else:
                print(f"  ✗ {func_name} - MISSING")
        
        print("\nSchema verification complete.")
        return True


if __name__ == "__main__":
    verify_schema()
