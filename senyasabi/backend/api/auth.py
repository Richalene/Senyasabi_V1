"""Auth endpoints: a thin proxy to Supabase Auth (GoTrue).

Passwords exist only in Supabase. The proxy exists so the desktop client needs no
Supabase keys, and so username->email resolution is never exposed to anonymous callers.
"""
import logging
import re
import time

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from ..config import SUPABASE_URL, SUPABASE_ANON_KEY
from ..database.postgre_session import get_postgres_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,30}$")   # stored lower-cased by the DB trigger
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8
BAD_LOGIN = "Invalid username/email or password."


class RegisterBody(BaseModel):
    username: str = Field(max_length=50)
    email: str = Field(max_length=255)
    password: str = Field(max_length=128)
    display_name: str | None = Field(default=None, max_length=100)


class LoginBody(BaseModel):
    identifier: str = Field(max_length=255)
    password: str = Field(max_length=128)


class RefreshBody(BaseModel):
    refresh_token: str = Field(max_length=2048)


def _gotrue(path: str, body: dict) -> requests.Response:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise HTTPException(503, "Authentication is not configured")
    try:
        return requests.post(
            f"{SUPABASE_URL}/auth/v1{path}", json=body, timeout=10,
            headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
        )
    except requests.exceptions.RequestException:
        raise HTTPException(502, "Authentication service unreachable")


def _error_code(resp: requests.Response) -> str:
    try:
        data = resp.json()
        return str(data.get("error_code") or data.get("error") or "")
    except ValueError:
        return ""


def _tokens(data: dict) -> dict:
    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": data.get("expires_at") or int(time.time()) + int(data.get("expires_in", 3600)),
    }


def _email_for_username(username: str) -> str | None:
    with get_postgres_session() as db:
        return db.execute(
            text("SELECT email FROM public.users WHERE lower(username) = :u"),
            {"u": username},
        ).scalar()


def _profile(user_id: str) -> dict:
    with get_postgres_session() as db:
        row = db.execute(
            text("SELECT user_id, username, email, display_name FROM public.users "
                 "WHERE user_id = :id"),
            {"id": user_id},
        ).mappings().first()
    if row is None:
        logger.error("auth user %s has no public.users row (trigger missing?)", user_id)
        raise HTTPException(502, "Profile not found")
    return {**row, "user_id": str(row["user_id"])}


@router.post("/register", status_code=201)
def register(body: RegisterBody):
    username = body.username.strip().lower()
    email = body.email.strip().lower()
    if not USERNAME_RE.match(username):
        raise HTTPException(400, "Username must be 3-30 characters: letters, numbers, . _ -")
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Enter a valid email address.")
    if len(body.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(400, f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    display_name = (body.display_name or "").strip() or username

    # The sign-up trigger silently falls back to a generated username on collision,
    # so reject duplicates up front.
    with get_postgres_session() as db:
        taken = db.execute(
            text("SELECT 1 FROM public.users WHERE lower(username) = :u"), {"u": username}
        ).first()
    if taken:
        raise HTTPException(409, "Username is already taken.")

    resp = _gotrue("/signup", {
        "email": email, "password": body.password,
        "data": {"username": username, "display_name": display_name},
    })
    if resp.status_code >= 400:
        code = _error_code(resp)
        if code in ("user_already_exists", "email_exists"):
            raise HTTPException(409, "Email is already registered.")
        if code == "weak_password":
            raise HTTPException(400, "Password is too weak.")
        if resp.status_code == 429:
            raise HTTPException(429, "Too many attempts. Try again later.")
        logger.error("signup failed: %s %s", resp.status_code, resp.text[:200])
        raise HTTPException(502, "Could not create account.")

    return {
        "username": username, "email": email, "display_name": display_name,
        # No access_token in the response means email confirmation is required.
        "needs_confirmation": "access_token" not in resp.json(),
    }


@router.post("/login")
def login(body: LoginBody):
    identifier = body.identifier.strip().lower()
    if not identifier or not body.password:
        raise HTTPException(400, "Username/email and password are required.")

    email = identifier if "@" in identifier else _email_for_username(identifier)
    if email is None:                       # same answer as a wrong password
        raise HTTPException(401, BAD_LOGIN)

    resp = _gotrue("/token?grant_type=password", {"email": email, "password": body.password})
    if resp.status_code >= 400:
        code = _error_code(resp)
        if code == "email_not_confirmed":
            raise HTTPException(403, "Please confirm your email before signing in.")
        if resp.status_code == 429:
            raise HTTPException(429, "Too many attempts. Try again later.")
        if resp.status_code in (400, 401, 422):
            raise HTTPException(401, BAD_LOGIN)
        logger.error("login failed: %s %s", resp.status_code, resp.text[:200])
        raise HTTPException(502, "Authentication service error")

    data = resp.json()
    return {"session": _tokens(data), "profile": _profile(data["user"]["id"])}


@router.post("/refresh")
def refresh(body: RefreshBody):
    resp = _gotrue("/token?grant_type=refresh_token", {"refresh_token": body.refresh_token})
    if resp.status_code in (400, 401):
        raise HTTPException(401, "Session expired. Please sign in again.")
    if resp.status_code >= 400:
        raise HTTPException(502, "Authentication service error")
    return {"session": _tokens(resp.json())}