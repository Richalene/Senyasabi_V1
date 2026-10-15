"""PostgreSQL session factory for FastAPI backend.

This provides a separate SQLAlchemy session for PostgreSQL (authoritative store),
distinct from the SQLite session used for local caching.

Uses Supabase Session Pooler for connection pooling.
Session pooler is optimized for serverless and transaction-based workloads.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from ..config import POSTGRESQL_URL

# Create PostgreSQL engine
# Using Supabase Session Pooler mode
# Session pooler is designed for short-lived connections and serverless environments
if POSTGRESQL_URL:
    postgres_engine = create_engine(
        POSTGRESQL_URL,
        echo=False,  # Set to True for SQL query logging
        future=True,
        # Session pooler manages connections, so we use minimal pooling settings
        pool_pre_ping=True,  # Verify connections before using
        pool_size=1,  # Session pooler handles pooling
        max_overflow=0,  # Session pooler handles overflow
        # Important for session pooler: connections should be short-lived
        pool_recycle=3600,  # Recycle connections after 1 hour
    )
else:
    postgres_engine = None
    print("Warning: POSTGRESQL_URL not set. PostgreSQL features will be unavailable.")

# Create session factory
PostgreSQLSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=postgres_engine
) if postgres_engine else None


def get_postgres_session() -> Session:
    """
    Get a PostgreSQL session for FastAPI endpoints.
    
    This should be used as a dependency in FastAPI routes.
    For Supabase session pooler, ensure sessions are short-lived and committed/rolled back promptly.
    
    Returns:
        SQLAlchemy Session for PostgreSQL
        
    Raises:
        RuntimeError: If POSTGRESQL_URL is not configured
    """
    if not PostgreSQLSessionLocal:
        raise RuntimeError("PostgreSQL is not configured. Set POSTGRESQL_URL environment variable.")
    
    return PostgreSQLSessionLocal()
