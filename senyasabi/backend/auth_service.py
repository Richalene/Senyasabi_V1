"""Authentication boundary using SQLite persistence and OS secure credential store."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone, timedelta
import re
from typing import Protocol
from uuid import uuid4

from argon2 import PasswordHasher, Type
from argon2.exceptions import VerificationError

from .database.session import get_session
from .database.models import User, OfflineAuth
from .database.repository import (
    create_user,
    get_user_by_username,
    create_offline_auth,
    get_offline_auth_by_username,
    update_offline_auth,
    record_failed_login_attempt,
    reset_failed_login_attempts,
    lock_offline_auth,
)
from .credential_store import get_credential_store


class AuthError(ValueError):
    """Safe authentication/validation message for the UI."""


@dataclass(frozen=True)
class User:
    user_id: int
    username: str
    password_hash: str
    display_name: str
    updated_at: datetime


class UserRepository(Protocol):
    def find_by_identifier(self, identifier: str) -> User | None: ...
    def add(self, user: User) -> None: ...


class SQLiteUserRepository:
    """SQLite-based user repository for persistence."""

    def find_by_identifier(self, identifier: str) -> User | None:
        with get_session() as db:
            user = get_user_by_username(db, identifier)

            if user is None:
                return None

            return User(
                user_id=user.user_id,
                username=user.username,
                password_hash=user.password_hash,
                display_name=user.display_name or "",
                updated_at=user.updated_at,
            )

    def add(self, user: User) -> None:
        with get_session() as db:
            create_user(
                db,
                user_id=user.user_id,
                username=user.username,
                display_name=user.display_name,
            )


_repository: UserRepository = SQLiteUserRepository()
_hasher = PasswordHasher(type=Type.ID)
_current_user: dict | None = None


def _public_user(user: User) -> dict:
    result = asdict(user)
    del result["password_hash"]
    return result


def register_user(username, password, display_name=None):
    username = username.strip()
    if not username or not password or not password.strip():
        raise AuthError("Username and password are required.")
    if "@" in username:
        raise AuthError("Username cannot contain @.")
    if _repository.find_by_identifier(username):
        raise AuthError("Username is already registered.")
    now = datetime.now(timezone.utc)
    user = User(
        user_id=0,  # Will be assigned by database (autoincrement)
        username=username,
        password_hash=_hasher.hash(password),
        display_name=(display_name or "").strip() or username,
        updated_at=now,
    )
    _repository.add(user)
    return _public_user(user)


def authenticate_user(identifier, password):
    global _current_user
    _current_user = None
    if not identifier.strip() or not password:
        raise AuthError("Username/email and password are required.")

    # First try online authentication via users table
    user = _repository.find_by_identifier(identifier)
    if user is None:
        raise AuthError("Invalid username/email or password.")

    try:
        _hasher.verify(user.password_hash, password)
    except VerificationError:
        raise AuthError("Invalid username/email or password.") from None

    _current_user = _public_user(user)

    # Update offline auth on successful login
    with get_session() as db:
        offline_auth = get_offline_auth_by_username(db, user.username)
        if offline_auth is None:
            # Create offline auth entry with password verifier
            password_verifier = _hasher.hash(password)
            create_offline_auth(
                db,
                user_id=user.user_id,
                username=user.username,
                password_verifier=password_verifier,
            )
        else:
            # Update last online login and reset failed attempts
            update_offline_auth(db, user.user_id, last_online_login=datetime.now())
            reset_failed_login_attempts(db, user.user_id)

    return dict(_current_user)


def authenticate_offline(username, password):
    """Authenticate using offline credentials when network is unavailable."""
    global _current_user
    _current_user = None
    if not username.strip() or not password:
        raise AuthError("Username and password are required.")

    with get_session() as db:
        offline_auth = get_offline_auth_by_username(db, username)
        if offline_auth is None:
            raise AuthError("No offline credentials found. Please login online first.")

        # Check if account is locked
        if offline_auth.locked_until and offline_auth.locked_until > datetime.now():
            raise AuthError("Account is temporarily locked due to too many failed attempts.")

        try:
            _hasher.verify(offline_auth.password_verifier, password)
        except VerificationError:
            # Record failed attempt
            record_failed_login_attempt(db, offline_auth.user_id)

            # Lock after 5 failed attempts
            if offline_auth.failed_attempts >= 5:
                lock_until = datetime.now() + timedelta(minutes=15)
                lock_offline_auth(db, offline_auth.user_id, lock_until)
                raise AuthError("Too many failed attempts. Account locked for 15 minutes.")
            else:
                raise AuthError("Invalid username or password.") from None

        # Reset failed attempts on successful login
        reset_failed_login_attempts(db, offline_auth.user_id)

        # Get the full user data
        user = _repository.find_by_identifier(username)
        if user is None:
            raise AuthError("User not found.")

        _current_user = _public_user(user)
        return dict(_current_user)


def logout_user():
    global _current_user
    _current_user = None


def get_current_user():
    return dict(_current_user) if _current_user is not None else None


def update_offline_password(user_id: int, new_password: str):
    """Update offline password verifier when user changes password online."""
    password_verifier = _hasher.hash(new_password)
    with get_session() as db:
        update_offline_auth(db, user_id, password_verifier=password_verifier)


def store_refresh_token(user_id: int, refresh_token: str) -> bool:
    """
    Store a refresh token in the OS secure credential store.

    Args:
        user_id: The user's ID
        refresh_token: The refresh token to store

    Returns:
        True if successful, False otherwise
    """
    credential_store = get_credential_store()
    return credential_store.store_refresh_token(user_id, refresh_token)


def get_refresh_token(user_id: int) -> str | None:
    """
    Retrieve a refresh token from the OS secure credential store.

    Args:
        user_id: The user's ID

    Returns:
        The refresh token if found, None otherwise
    """
    credential_store = get_credential_store()
    return credential_store.get_refresh_token(user_id)


def delete_refresh_token(user_id: int) -> bool:
    """
    Delete a refresh token from the OS secure credential store.

    Args:
        user_id: The user's ID

    Returns:
        True if successful, False otherwise
    """
    credential_store = get_credential_store()
    return credential_store.delete_refresh_token(user_id)
