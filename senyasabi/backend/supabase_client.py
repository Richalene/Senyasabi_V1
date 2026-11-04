"""Supabase client for direct anon access (fallback mode).

This provides a Supabase client for direct database/auth access when running
in direct mode (SYSTEM_MODE=direct). In distributed mode (default), the app
uses FastAPI with anon key and only falls back to direct Supabase if FastAPI
is unavailable. In fastapi mode (development), this returns None and the app
uses the FastAPI proxy with service role key.
"""
import inspect
import logging
import os
from . import config
from .config import SUPABASE_URL, SUPABASE_ANON_KEY, CLIENT_MODE

logger = logging.getLogger(__name__)
_supabase_client = None
_UNSET = object()
_INITIAL_CLIENT_MODE = CLIENT_MODE
_INITIAL_URL = SUPABASE_URL
_INITIAL_KEY = SUPABASE_ANON_KEY


def _ensure_httpx_proxy_compatibility():
    """
    Ensure compatibility between gotrue (which passes proxy=...)
    and httpx < 0.26 (which expects proxies=...).
    """
    try:
        import httpx
        init = httpx.Client.__init__
        sig = inspect.signature(init)
        if "proxy" not in sig.parameters and "proxies" in sig.parameters:
            if not getattr(httpx.Client, "_proxy_compat_applied", False):
                def _compat_init(self, *args, **kwargs):
                    if "proxy" in kwargs and "proxies" not in kwargs:
                        kwargs["proxies"] = kwargs.pop("proxy")
                    return init(self, *args, **kwargs)
                httpx.Client.__init__ = _compat_init
                httpx.Client._proxy_compat_applied = True
    except Exception as exc:
        logger.debug("Proxy compatibility check skipped: %s", type(exc).__name__)


def _get_client_mode() -> str:
    """Get the active client mode, checking test overrides, env, or config."""
    import sys
    this_mod = sys.modules.get(__name__)
    if this_mod:
        current_mod_val = getattr(this_mod, "CLIENT_MODE", None)
        if current_mod_val != _INITIAL_CLIENT_MODE and current_mod_val is not None:
            return str(current_mod_val).lower()
    env_mode = os.getenv("SYSTEM_MODE") or os.getenv("SENYASABI_CLIENT_MODE")
    if env_mode:
        return env_mode.lower()
    return str(CLIENT_MODE).lower()


def _get_credentials() -> tuple[str | None, str | None]:
    """Get Supabase URL and anon key, checking test overrides, env, or config."""
    import sys
    this_mod = sys.modules.get(__name__)
    url = getattr(this_mod, "SUPABASE_URL", _UNSET) if this_mod else _UNSET
    if url is _UNSET or (url == _INITIAL_URL and os.getenv("SUPABASE_URL") is not None):
        url = os.getenv("SUPABASE_URL") or getattr(config, "SUPABASE_URL", None)

    key = getattr(this_mod, "SUPABASE_ANON_KEY", _UNSET) if this_mod else _UNSET
    if key is _UNSET or (key == _INITIAL_KEY and os.getenv("SUPABASE_ANON_KEY") is not None):
        key = os.getenv("SUPABASE_ANON_KEY") or getattr(config, "SUPABASE_ANON_KEY", None)

    return url, key


def get_supabase_client():
    """
    Get Supabase client for direct anon/authenticated access.
    
    Returns:
        Supabase client instance if in direct, supabase, or distributed mode and configured
        None if in fastapi mode (uses FastAPI backend exclusively) or credentials missing in distributed mode
        
    Raises:
        RuntimeError: If in direct/supabase mode but credentials not configured or library missing
    """
    global _supabase_client
    
    mode = _get_client_mode()
    
    # In fastapi mode, use FastAPI backend exclusively
    if mode == "fastapi":
        return None
    
    # Supported modes for direct/fallback Supabase access
    if mode not in ("direct", "distributed", "supabase"):
        logger.warning("Unknown CLIENT_MODE: %s, defaulting to None", mode)
        return None
    
    url, anon_key = _get_credentials()
    
    # Check if credentials are configured
    if not url or not anon_key:
        if mode in ("direct", "supabase"):
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_ANON_KEY must be configured for direct mode. "
                "Set these in your .env file or environment variables."
            )
        logger.warning("Supabase credentials not configured; direct Supabase fallback is disabled")
        return None
    
    # Lazy initialization
    if _supabase_client is None:
        try:
            _ensure_httpx_proxy_compatibility()
            from supabase import create_client
            # Don't pass options to avoid proxy parameter incompatibility
            _supabase_client = create_client(url, anon_key)
            # Store URL for use in media service
            _supabase_client.supabase_url = url
        except ImportError:
            if mode in ("direct", "supabase"):
                raise RuntimeError(
                    "supabase library not installed. "
                    "Install with: pip install supabase"
                )
            logger.warning("supabase library not installed; fallback disabled")
            return None
        except TypeError as e:
            # Handle API compatibility issues with newer supabase versions
            logger.warning("Supabase client initialization failed (API compatibility): %s", type(e).__name__)
            _supabase_client = None
            return None
        except Exception as e:
            logger.warning("Supabase client initialization failed: %s", type(e).__name__)
            _supabase_client = None
            return None
    
    return _supabase_client


def is_supabase_available() -> bool:
    """
    Check if Supabase client is available for use.
    
    Returns:
        True if configured and in a mode that supports Supabase (direct, supabase, distributed),
        False otherwise (e.g. fastapi mode or missing credentials).
    """
    mode = _get_client_mode()
    if mode not in ("direct", "distributed", "supabase"):
        return False
    url, anon_key = _get_credentials()
    return bool(url and anon_key)


def reset_client():
    """
    Reset the Supabase client (useful for testing).
    """
    global _supabase_client
    _supabase_client = None
