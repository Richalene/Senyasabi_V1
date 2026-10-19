"""Direct Supabase Auth client for distributed mode.

This module provides direct Supabase Auth API calls when running in
distributed mode (SENYESABI_MODE=distributed). It bypasses the FastAPI proxy
and talks directly to Supabase Auth using the anon key.
"""
import time
from typing import Protocol

from ..config import SUPABASE_URL, SUPABASE_ANON_KEY
from ..supabase_client import get_supabase_client


class AuthError(ValueError):
    """Safe authentication/validation message for the UI."""


class NetworkError(Exception):
    """Server unreachable or failing (5xx) - the caller may fall back to offline."""


def _ensure_supabase():
    """Ensure Supabase client is available."""
    client = get_supabase_client()
    if client is None:
        raise NetworkError("Supabase client not available")
    return client


def register(username, email, password, display_name=None) -> dict:
    """
    Register a new user with Supabase Auth.
    
    Args:
        username: Username (3-30 characters, lowercase)
        email: Email address
        password: Password (min 8 characters)
        display_name: Optional display name
        
    Returns:
        Dict with username, email, display_name, needs_confirmation flag
        
    Raises:
        AuthError: If registration fails due to validation
        NetworkError: If Supabase is unreachable
    """
    try:
        supabase = _ensure_supabase()
        
        # Prepare user metadata
        metadata = {"username": username}
        if display_name:
            metadata["display_name"] = display_name
        
        # Sign up with Supabase
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": metadata
            }
        })
        
        # Check if email confirmation is required
        needs_confirmation = not hasattr(response, 'session') or response.session is None
        
        return {
            "username": username,
            "email": email,
            "display_name": display_name or username,
            "needs_confirmation": needs_confirmation
        }
        
    except Exception as e:
        error_msg = str(e)
        
        # Map Supabase errors to our AuthError
        if "User already registered" in error_msg or "user_already_exists" in error_msg.lower():
            raise AuthError("Email is already registered.")
        elif "weak_password" in error_msg.lower():
            raise AuthError("Password is too weak.")
        elif "rate limit" in error_msg.lower():
            raise AuthError("Too many attempts. Try again later.")
        elif "invalid" in error_msg.lower() or "validation" in error_msg.lower():
            raise AuthError("Invalid input. Please check your details.")
        else:
            # Treat other errors as network errors
            raise NetworkError(f"Registration failed: {error_msg}")


def login(identifier, password) -> dict:
    """
    Sign in a user with Supabase Auth.
    
    Args:
        identifier: Username or email
        password: User password
        
    Returns:
        Dict with session (access_token, refresh_token, expires_at) and profile
        
    Raises:
        AuthError: If credentials are invalid
        NetworkError: If Supabase is unreachable
    """
    try:
        supabase = _ensure_supabase_client()
        
        # Determine if identifier is email or username
        # For Supabase, we need email, so we'll try username lookup
        # This is handled by the caller in auth_service
        
        # Sign in with email and password
        response = supabase.auth.sign_in_with_password({
            "email": identifier,
            "password": password
        })
        
        # Extract session data
        session = response.session
        tokens = {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "expires_at": session.expires_at or int(time.time()) + 3600
        }
        
        # Extract user profile
        user = response.user
        profile = {
            "user_id": user.id,
            "username": user.user_metadata.get("username", user.email.split("@")[0]),
            "email": user.email,
            "display_name": user.user_metadata.get("display_name") or user.user_metadata.get("username")
        }
        
        return {
            "session": tokens,
            "profile": profile
        }
        
    except Exception as e:
        error_msg = str(e)
        
        # Map Supabase errors to our AuthError
        if "invalid login credentials" in error_msg.lower() or "invalid_grant" in error_msg.lower():
            raise AuthError("Invalid username/email or password.")
        elif "email not confirmed" in error_msg.lower():
            raise AuthError("Please confirm your email before signing in.")
        elif "rate limit" in error_msg.lower():
            raise AuthError("Too many attempts. Try again later.")
        else:
            # Treat other errors as network errors
            raise NetworkError(f"Login failed: {error_msg}")


def refresh(refresh_token) -> dict:
    """
    Refresh an access token using a refresh token.
    
    Args:
        refresh_token: The refresh token from previous session
        
    Returns:
        Dict with new session (access_token, refresh_token, expires_at)
        
    Raises:
        AuthError: If refresh token is invalid or expired
        NetworkError: If Supabase is unreachable
    """
    try:
        supabase = _ensure_supabase_client()
        
        # Refresh the session
        response = supabase.auth.refresh_session(refresh_token)
        
        session = response.session
        tokens = {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "expires_at": session.expires_at or int(time.time()) + 3600
        }
        
        return {"session": tokens}
        
    except Exception as e:
        error_msg = str(e)
        
        if "invalid" in error_msg.lower() or "expired" in error_msg.lower():
            raise AuthError("Session expired. Please sign in again.")
        else:
            raise NetworkError(f"Token refresh failed: {error_msg}")


def get_user_by_email(email: str) -> dict | None:
    """
    Get user profile by email (for username lookup).
    
    This queries the users table to find the username associated with an email.
    
    Args:
        email: Email address to look up
        
    Returns:
        User profile dict or None if not found
    """
    try:
        supabase = _ensure_supabase_client()
        
        # Query users table (this requires RLS policy for authenticated users)
        # For anon, this won't work - handled by caller falling back to FastAPI
        response = supabase.table('users').select('user_id, username, email, display_name').eq('email', email).execute()
        
        if response.data:
            user = response.data[0]
            return {
                "user_id": user['user_id'],
                "username": user['username'],
                "email": user['email'],
                "display_name": user.get('display_name') or user['username']
            }
        return None
        
    except Exception:
        # If this fails (e.g., RLS blocks anon), return None
        return None


def get_user_by_username(username: str) -> dict | None:
    """
    Get user profile by username.
    
    This queries the users table to find the email associated with a username.
    
    Args:
        username: Username to look up
        
    Returns:
        User profile dict or None if not found
    """
    try:
        supabase = _ensure_supabase_client()
        
        # Query users table by username (case-insensitive)
        response = supabase.table('users').select('user_id, username, email, display_name').ilike('username', username).execute()
        
        if response.data:
            user = response.data[0]
            return {
                "user_id": user['user_id'],
                "username": user['username'],
                "email": user['email'],
                "display_name": user.get('display_name') or user['username']
            }
        return None
        
    except Exception:
        # If this fails (e.g., RLS blocks anon), return None
        return None
