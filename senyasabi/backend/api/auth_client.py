"""HTTP calls to the /auth endpoints. Distinguishes 'rejected' from 'unreachable'."""
import requests

from ..config import API_BASE_URL

TIMEOUT = 8


class AuthError(ValueError):
    """Safe authentication/validation message for the UI."""


class NetworkError(Exception):
    """Server unreachable or failing (5xx) - the caller may fall back to offline."""


def _post(path: str, payload: dict) -> dict:
    try:
        resp = requests.post(f"{API_BASE_URL}/api/v1/auth{path}", json=payload, timeout=TIMEOUT)
    except requests.exceptions.RequestException as exc:
        raise NetworkError(str(exc)) from exc
    if resp.status_code >= 500:
        raise NetworkError(f"server returned {resp.status_code}")
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail")
        except ValueError:
            detail = None
        raise AuthError(detail if isinstance(detail, str) else "Request was rejected.")
    return resp.json()


def register(username, email, password, display_name=None) -> dict:
    return _post("/register", {"username": username, "email": email,
                               "password": password, "display_name": display_name})


def login(identifier, password) -> dict:
    return _post("/login", {"identifier": identifier, "password": password})


def refresh(refresh_token) -> dict:
    return _post("/refresh", {"refresh_token": refresh_token})