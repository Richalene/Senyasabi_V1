"""Supabase client for direct anon access (fallback mode).

This provides a Supabase client for direct database/auth access when running
in direct mode (SYSTEM_MODE=direct). In distributed mode (default), the app
uses FastAPI with anon key and only falls back to direct Supabase if FastAPI
is unavailable. In fastapi mode (development), this returns None and the app
uses the FastAPI proxy with service role key.
"""
import logging
from .config import SUPABASE_URL, SUPABASE_ANON_KEY, CLIENT_MODE

logger = logging.getLogger(__name__)
_supabase_client = None


def get_supabase_client():
    """
    Get Supabase client for direct anon/authenticated access.
    
    Returns:
        Supabase client instance if in direct mode and configured
        None if in fastapi or distributed mode (use FastAPI backend)
        
    Raises:
        RuntimeError: If in direct mode but credentials not configured
    """
    global _supabase_client
    
    # In fastapi or distributed mode, use FastAPI backend by default
    if CLIENT_MODE in ("fastapi", "distributed"):
        return None
    
    # In direct mode, use Supabase client
    if CLIENT_MODE != "direct":
        logger.warning(f"Unknown CLIENT_MODE: {CLIENT_MODE}, defaulting to None")
        return None
    
    # Check if credentials are configured
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be configured for direct mode. "
            "Set these in your .env file or environment variables."
        )
    
    # Lazy initialization
    if _supabase_client is None:
        try:
            from supabase import create_client
            # Don't pass options to avoid proxy parameter incompatibility
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            # Store URL for use in media service
            _supabase_client.supabase_url = SUPABASE_URL
        except ImportError:
            raise RuntimeError(
                "supabase library not installed. "
                "Install with: pip install supabase"
            )
        except TypeError as e:
            # Handle API compatibility issues with newer supabase versions
            logger.warning("Supabase client initialization failed (API compatibility): %s", e)
            logger.warning("Direct mode will be disabled")
            _supabase_client = None
            return None
    
    return _supabase_client


def is_supabase_available() -> bool:
    """
    Check if Supabase client is available for use.
    
    Returns:
        True if in direct mode and configured, False otherwise
    """
    if CLIENT_MODE != "direct":
        return False
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY)


def reset_client():
    """
    Reset the Supabase client (useful for testing).
    """
    global _supabase_client
    _supabase_client = None
