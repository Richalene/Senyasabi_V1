"""Authentication boundary.

Online:  desktop -> FastAPI /auth/* -> Supabase Auth (the password lives only there).
Offline: argon2id verifier saved in SQLite (or injected UserRepository for tests).
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import re
import time
from typing import Protocol
import uuid
from uuid import uuid4

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError

from .config import CLIENT_MODE

# Import appropriate auth client based on mode
if CLIENT_MODE == "distributed":
    from .api.auth_client_distributed import AuthError, NetworkError
    auth_client = __import__('backend.api.auth_client_distributed', fromlist=[''])
else:
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

__all__ = [
    "AuthError", "NetworkError", "User", "UserRepository",
    "InMemoryUserRepository", "SQLiteUserRepository",
    "register_user", "authenticate_user", "authenticate_offline",
    "establish_session", "logout_user", "get_current_user", "get_access_token",
]

USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,30}$")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
MIN_PASSWORD_LENGTH = 8
INVALID = "Invalid username/email or password."
TOKEN_REFRESH_MARGIN = 60  # seconds


@dataclass(frozen=True)
class User:
    user_id: str
    username: str
    email: str
    password_hash: str
    display_name: str
    notifications_enabled: bool
    dark_mode: bool
    created_at: datetime
    updated_at: datetime


class UserRepository(Protocol):
    def find_by_identifier(self, identifier: str) -> User | None: ...
    def add(self, user: User) -> None: ...


class InMemoryUserRepository:
    def __init__(self):
        self._users: dict[str, User] = {}

    def find_by_identifier(self, identifier: str) -> User | None:
        key = identifier.strip().casefold()
        return next((user for user in self._users.values()
                     if key in (user.username.casefold(), user.email.casefold())), None)

    def add(self, user: User) -> None:
        if self.find_by_identifier(user.username):
            raise AuthError("Username is already registered.")
        if self.find_by_identifier(user.email):
            raise AuthError("Email is already registered.")
        self._users[user.user_id] = user


class SQLiteUserRepository:
    """SQLite-backed user repository bridging local offline_auth and users tables."""

    def find_by_identifier(self, identifier: str) -> User | None:
        key = (identifier or "").strip()
        if not key:
            return None
        try:
            with session_scope() as db:
                offline = repo.get_offline_auth_by_identifier(db, key)
                if offline is not None and offline.user is not None:
                    u = offline.user
                    return User(
                        user_id=str(u.user_id),
                        username=u.username,
                        email=u.email or "",
                        password_hash=offline.password_verifier,
                        display_name=u.display_name or u.username,
                        notifications_enabled=True,
                        dark_mode=False,
                        created_at=u.updated_at or _utcnow(),
                        updated_at=u.updated_at or _utcnow(),
                    )
                u = repo.get_user_by_email(db, key) if "@" in key else repo.get_user_by_username(db, key)
                if u is None:
                    return None
                return User(
                    user_id=str(u.user_id),
                    username=u.username,
                    email=u.email or "",
                    password_hash="",
                    display_name=u.display_name or u.username,
                    notifications_enabled=True,
                    dark_mode=False,
                    created_at=u.updated_at or _utcnow(),
                    updated_at=u.updated_at or _utcnow(),
                )
        except Exception:
            return None

    def add(self, user: User) -> None:
        if self.find_by_identifier(user.username):
            raise AuthError("Username is already registered.")
        if self.find_by_identifier(user.email):
            raise AuthError("Email is already registered.")
        uid = uuid.UUID(str(user.user_id))
        with session_scope() as db:
            repo.upsert_user(db, uid, user.username, user.email, user.display_name)
            repo.upsert_offline_auth(db, uid, user.password_hash, user.updated_at)


_repository: UserRepository = SQLiteUserRepository()
_hasher = PasswordHasher(type=Type.ID)
_current_user: dict | None = None
_session: dict | None = None  # {"access_token", "refresh_token", "expires_at"}; None when offline
_pending_tokens: dict[str, dict] = {}  # user_id -> tokens from a background login awaiting establish_session()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _public_user(user) -> dict:
    if isinstance(user, User):
        result = asdict(user)
        del result["password_hash"]
        return result
    # SQLAlchemy model: user_id stays a uuid.UUID for Uuid columns
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name or user.username,
        "notifications_enabled": True,
        "dark_mode": False,
        "updated_at": user.updated_at,
    }


def _clear_session() -> None:
    global _current_user, _session
    _current_user = None
    _session = None
    _pending_tokens.clear()


def _apply_tokens(user_id: uuid.UUID, tokens: dict) -> None:
    global _session
    _session = dict(tokens)
    get_credential_store().store_refresh_token(str(user_id), tokens["refresh_token"])


# ── registration ──────────────────────────────────────────────────────────────

def register_user(username, email, password, display_name=None) -> dict:
    username = (username or "").strip()
    email = (email or "").strip()
    if not username or not email or not password or not password.strip():
        raise AuthError("Username, email and password are required.")
    if "@" in username:
        raise AuthError("Username cannot contain @.")
    if not EMAIL_RE.fullmatch(email):
        raise AuthError("Enter a valid email address.")
    if _repository.find_by_identifier(username):
        raise AuthError("Username is already registered.")
    if _repository.find_by_identifier(email):
        raise AuthError("Email is already registered.")

    if isinstance(_repository, InMemoryUserRepository):
        now = _utcnow()
        user = User(
            str(uuid4()), username, email, _hasher.hash(password),
            (display_name or "").strip() or username, True, False, now, now,
        )
        _repository.add(user)
        return _public_user(user)

    norm_username = username.lower()
    norm_email = repo.normalize_email(email)
    if not USERNAME_RE.match(norm_username):
        raise AuthError("Username must be 3-30 characters: letters, numbers, . _ -")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AuthError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    try:
        # -> {"username", "email", "display_name", "needs_confirmation"}
        return auth_client.register(norm_username, norm_email, password,
                                    (display_name or "").strip() or None)
    except NetworkError:
        now = _utcnow()
        user = User(
            str(uuid4()), norm_username, norm_email, _hasher.hash(password),
            (display_name or "").strip() or norm_username, True, False, now, now,
        )
        _repository.add(user)
        return _public_user(user)


# ── sign-in ───────────────────────────────────────────────────────────────────

def authenticate_user(identifier, password, *, establish_session=True) -> dict:
    """Verify credentials, optionally publishing the session for synchronous callers.

    Background jobs must pass ``establish_session=False`` and let their live UI
    callback publish the result. A cancelled job can then finish without
    restoring a session after the learner has navigated away or logged out.
    """
    global _current_user
    if establish_session:
        _clear_session()
    identifier = (identifier or "").strip()
    if not identifier or not password:
        raise AuthError("Username/email and password are required.")

    if isinstance(_repository, InMemoryUserRepository):
        user = _repository.find_by_identifier(identifier)
        if user is None:
            raise AuthError(INVALID)
        try:
            _hasher.verify(user.password_hash, password)
        except (VerificationError, InvalidHashError):
            raise AuthError(INVALID) from None
        public_user = _public_user(user)
        if establish_session:
            _current_user = dict(public_user)
        return public_user

    # In distributed mode, if identifier is username, we need to look up email
    login_identifier = identifier
    if CLIENT_MODE == "distributed" and "@" not in identifier:
        try:
            from .api.auth_client_distributed import get_user_by_username
            # Try to get email from username
            user = get_user_by_username(identifier)
            if user:
                login_identifier = user["email"]
        except Exception:
            # Fall through to existing logic (will try offline)
            pass

    try:
        data = auth_client.login(login_identifier, password)
    except NetworkError:
        return authenticate_offline(identifier, password, establish_session=establish_session)
    return _complete_online_login(data, password, establish_session=establish_session)


def _complete_online_login(data: dict, password: str, *, establish_session=True) -> dict:
    global _current_user
    profile = data["profile"]
    user_id = uuid.UUID(profile["user_id"])
    verifier = _hasher.hash(password)  # refreshed every online login

    with session_scope() as db:
        user = repo.upsert_user(db, user_id, profile["username"],
                                profile.get("email"), profile.get("display_name"))
        repo.upsert_offline_auth(db, user_id, verifier, _utcnow())
        public = _public_user(user)

    if establish_session:
        _current_user = dict(public)
        _apply_tokens(user_id, data["session"])
    else:
        # Background login: hold the tokens until the live UI callback calls establish_session().
        _pending_tokens[str(user_id)] = dict(data["session"])
    return dict(public)


def authenticate_offline(identifier, password, *, establish_session=True) -> dict:
    """Verify against the local argon2 verifier. Throttling state must survive failures,
    so errors are recorded inside the transaction and raised only after it commits."""
    global _current_user
    if establish_session:
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

    if establish_session:
        _current_user = dict(public)
        _restore_session(public["user_id"])
    return dict(public)


def establish_session(user) -> dict:
    """Publish a verified public user from a successful, still-active UI job."""
    global _current_user
    _current_user = {key: value for key, value in user.items()
                     if key not in ("password", "password_hash")}
    tokens = _pending_tokens.pop(str(_current_user.get("user_id")), None)
    if tokens:
        _apply_tokens(_current_user["user_id"], tokens)
    return dict(_current_user)


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
    had_session = _session is not None
    _clear_session()
    if user is not None and had_session:
        get_credential_store().delete_refresh_token(str(user["user_id"]))


def get_current_user() -> dict | None:
    return dict(_current_user) if _current_user is not None else None
