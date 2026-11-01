"""Supabase client for direct anon access (distributed client mode).

This provides a Supabase client for direct database/auth access when running
in distributed mode (SYSTEM_MODE=distributed). In fastapi mode, this
returns None and the app uses the FastAPI proxy instead.
"""
from .config import SUPABASE_URL, SUPABASE_ANON_KEY, CLIENT_MODE

_supabase_client = None


def get_supabase_client():
    """
    Get Supabase client for direct anon/authenticated access.
    
    Returns:
        Supabase client instance if in distributed mode and configured
        None if in fastapi mode or not configured
        
    Raises:
        RuntimeError: If in distributed mode but credentials not configured
    """
    global _supabase_client
    
    # In fastapi mode, we don't use Supabase client
    if CLIENT_MODE == "fastapi":
        return None
    
    # Check if credentials are configured
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be configured for distributed mode. "
            "Set these in your .env file or environment variables."
        )
    
    # Lazy initialization
    if _supabase_client is None:
        try:
            from supabase import create_client
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            # Store URL for use in media service
            _supabase_client.supabase_url = SUPABASE_URL
        except ImportError:
            raise RuntimeError(
                "supabase library not installed. "
                "Install with: pip install supabase"
            )
    
    return _supabase_client


def is_supabase_available() -> bool:
    """
    Check if Supabase client is available for use.
    
    Returns:
        True if in distributed mode and configured, False otherwise
    """
    if CLIENT_MODE == "fastapi":
        return False
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY)


def reset_client():
    """
    Reset the Supabase client (useful for testing).
    """
    global _supabase_client
    _supabase_client = None
