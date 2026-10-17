"""Authentication boundary.

Online:  desktop -> FastAPI /auth/* -> Supabase Auth (the password lives only there).
Offline: argon2id verifier saved in SQLite after each successful online login.
"""
import re
import time
import uuid
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError

from .api import auth_client
from .api.auth_client import AuthError, NetworkError  
from .config import (
    OFFLINE_AUTH_LOCKOUT_MINUTES,
    OFFLINE_AUTH_MAX_DAYS,
    OFFLINE_AUTH_MAX_FAILED_ATTEMPTS,
)
from .credential_store import get_credential_store
from .database import repository as repo
from .database.session import session_scope

__all__ = ["AuthError", "NetworkError", "register_user", "authenticate_user",
           "authenticate_offline", "logout_user", "get_current_user", "get_access_token"]

USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8
INVALID = "Invalid username/email or password."
TOKEN_REFRESH_MARGIN = 60  # seconds

_hasher = PasswordHasher(type=Type.ID)
_current_user: dict | None = None
_session: dict | None = None  # {"access_token", "refresh_token", "expires_at"}; None when offline


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _public_user(user) -> dict:
    # user_id stays a uuid.UUID: the repository's Uuid columns need real UUIDs
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name or user.username,
        "updated_at": user.updated_at,
    }


def _clear_session() -> None:
    global _current_user, _session
    _current_user = None
    _session = None


def _apply_tokens(user_id: uuid.UUID, tokens: dict) -> None:
    global _session
    _session = dict(tokens)
    get_credential_store().store_refresh_token(str(user_id), tokens["refresh_token"])


# ── registration ──────────────────────────────────────────────────────────────

def register_user(username, email, password, display_name=None) -> dict:
    username = (username or "").strip().lower()
    email = repo.normalize_email(email or "")
    if not username or not email or not password or not password.strip():
        raise AuthError("Username, email and password are required.")
    if not USERNAME_RE.match(username):
        raise AuthError("Username must be 3-30 characters: letters, numbers, . _ -")
    if not EMAIL_RE.match(email):
        raise AuthError("Enter a valid email address.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AuthError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    try:
        # -> {"username", "email", "display_name", "needs_confirmation"}
        return auth_client.register(username, email, password,
                                    (display_name or "").strip() or None)
    except NetworkError:
        raise AuthError(
            "Can't reach the server. Creating an account needs an internet connection."
        ) from None


# ── sign-in ───────────────────────────────────────────────────────────────────

def authenticate_user(identifier, password) -> dict:
    """Online first; offline only if the server is unreachable. A server 'no' is final."""
    _clear_session()
    identifier = (identifier or "").strip()
    if not identifier or not password:
        raise AuthError("Username/email and password are required.")
    try:
        data = auth_client.login(identifier, password)
    except NetworkError:
        return authenticate_offline(identifier, password)
    return _complete_online_login(data, password)


def _complete_online_login(data: dict, password: str) -> dict:
    global _current_user
    profile = data["profile"]
    user_id = uuid.UUID(profile["user_id"])
    verifier = _hasher.hash(password)  # refreshed every online login

    with session_scope() as db:
        user = repo.upsert_user(db, user_id, profile["username"],
                                profile.get("email"), profile.get("display_name"))
        repo.upsert_offline_auth(db, user_id, verifier, _utcnow())
        public = _public_user(user)

    _current_user = public
    _apply_tokens(user_id, data["session"])
    return dict(public)


def authenticate_offline(identifier, password) -> dict:
    """Verify against the local argon2 verifier. Throttling state must survive failures,
    so errors are recorded inside the transaction and raised only after it commits."""
    global _current_user
    _clear_session()
    identifier = (identifier or "").strip()
    if not identifier or not password:
        raise AuthError("Username/email and password are required.")

    now = _utcnow()
    error: str | None = None
    public: dict | None = None

    with session_scope() as db:
        offline = repo.get_offline_auth_by_identifier(db, identifier)
        if offline is None:
            error = "No offline credentials found. Please sign in online first."
        elif offline.locked_until and offline.locked_until > now:
            error = "Too many failed attempts. Try again later."
        elif now - offline.last_online_login > timedelta(days=OFFLINE_AUTH_MAX_DAYS):
            error = "Offline sign-in has expired. Connect to the internet and sign in again."
        else:
            try:
                _hasher.verify(offline.password_verifier, password)
            except (VerificationError, InvalidHashError):
                offline.failed_attempts += 1
                if offline.failed_attempts >= OFFLINE_AUTH_MAX_FAILED_ATTEMPTS:
                    offline.locked_until = now + timedelta(minutes=OFFLINE_AUTH_LOCKOUT_MINUTES)
                    offline.failed_attempts = 0
                    error = (f"Too many failed attempts. "
                             f"Locked for {OFFLINE_AUTH_LOCKOUT_MINUTES} minutes.")
                else:
                    error = INVALID
            else:
                offline.failed_attempts = 0
                offline.locked_until = None
                public = _public_user(offline.user)

    if error:
        raise AuthError(error)

    _current_user = public
    _restore_session(public["user_id"])
    return dict(public)


def _restore_session(user_id: uuid.UUID) -> None:
    """Best effort: after an offline sign-in, use the keyring refresh token to go online."""
    store = get_credential_store()
    token = store.get_refresh_token(str(user_id))
    if not token:
        return
    try:
        data = auth_client.refresh(token)
    except NetworkError:
        return                                   # still offline; try again on next token request
    except AuthError:
        store.delete_refresh_token(str(user_id))  # revoked/expired: password login needed
        return
    _apply_tokens(user_id, data["session"])


# ── session ───────────────────────────────────────────────────────────────────

def get_access_token() -> str | None:
    """Valid access token or None. Refreshes when close to expiry. api_client calls this."""
    global _session
    if _current_user is None:
        return None
    if _session is None:
        _restore_session(_current_user["user_id"])  # offline login earlier; retry now
        return _session["access_token"] if _session else None
    if _session["expires_at"] - time.time() > TOKEN_REFRESH_MARGIN:
        return _session["access_token"]
    try:
        data = auth_client.refresh(_session["refresh_token"])
    except NetworkError:
        return _session["access_token"] if _session["expires_at"] > time.time() else None
    except AuthError:
        get_credential_store().delete_refresh_token(str(_current_user["user_id"]))
        _session = None
        return None
    _apply_tokens(_current_user["user_id"], data["session"])
    return _session["access_token"]


def logout_user() -> None:
    user = _current_user
    _clear_session()
    if user is not None:
        get_credential_store().delete_refresh_token(str(user["user_id"]))


def get_current_user() -> dict | None:
    return dict(_current_user) if _current_user is not None else None