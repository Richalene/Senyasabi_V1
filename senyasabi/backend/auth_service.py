"""Authentication boundary. Replace _repository with a persistent repository later."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import re
from typing import Protocol
from uuid import uuid4

from argon2 import PasswordHasher, Type
from argon2.exceptions import VerificationError


class AuthError(ValueError):
    """Safe authentication/validation message for the UI."""


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


_repository: UserRepository = InMemoryUserRepository()
_hasher = PasswordHasher(type=Type.ID)
_current_user: dict | None = None


def _public_user(user: User) -> dict:
    result = asdict(user)
    del result["password_hash"]
    return result


def register_user(username, email, password, display_name=None):
    username, email = username.strip(), email.strip()
    if not username or not email or not password or not password.strip():
        raise AuthError("Username, email and password are required.")
    if "@" in username:
        raise AuthError("Username cannot contain @.")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise AuthError("Enter a valid email address.")
    if _repository.find_by_identifier(username):
        raise AuthError("Username is already registered.")
    if _repository.find_by_identifier(email):
        raise AuthError("Email is already registered.")
    now = datetime.now(timezone.utc)
    user = User(str(uuid4()), username, email, _hasher.hash(password),
                (display_name or "").strip() or username, True, False, now, now)
    _repository.add(user)
    return _public_user(user)


def authenticate_user(identifier, password):
    global _current_user
    _current_user = None
    if not identifier.strip() or not password:
        raise AuthError("Username/email and password are required.")
    user = _repository.find_by_identifier(identifier)
    if user is None:
        raise AuthError("Invalid username/email or password.")
    try:
        _hasher.verify(user.password_hash, password)
    except VerificationError:
        raise AuthError("Invalid username/email or password.") from None
    _current_user = _public_user(user)
    return dict(_current_user)


def logout_user():
    global _current_user
    _current_user = None


def get_current_user():
    return dict(_current_user) if _current_user is not None else None
