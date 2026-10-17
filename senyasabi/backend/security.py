"""JWT validation for Supabase Auth access tokens."""
import time
import uuid

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import SUPABASE_URL, SUPABASE_JWT_SECRET

security = HTTPBearer()

ISSUER = f"{SUPABASE_URL}/auth/v1" if SUPABASE_URL else None
JWKS_URL = f"{ISSUER}/.well-known/jwks.json" if ISSUER else None
ASYMMETRIC_ALGS = {"RS256", "ES256"}
JWKS_TTL = 600           # seconds
JWKS_MIN_REFETCH = 30    # don't hammer Supabase when a bad kid arrives

_jwks: dict = {"keys": {}, "fetched": 0.0}


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _signing_key(kid: str | None) -> dict | None:
    now = time.time()
    age = now - _jwks["fetched"]
    if age > JWKS_TTL or (kid not in _jwks["keys"] and age > JWKS_MIN_REFETCH):
        try:
            resp = requests.get(JWKS_URL, timeout=5)
            resp.raise_for_status()
            _jwks["keys"] = {k["kid"]: k for k in resp.json().get("keys", [])}
            _jwks["fetched"] = now
        except requests.exceptions.RequestException:
            if not _jwks["keys"]:
                raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                                    "Auth keys unavailable")
    return _jwks["keys"].get(kid)


async def validate_supabase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    if not ISSUER:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Auth is not configured")
    token = credentials.credentials
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")
        if alg == "HS256":                       # legacy projects: shared secret
            if not SUPABASE_JWT_SECRET:
                raise _unauthorized()
            key = SUPABASE_JWT_SECRET
        elif alg in ASYMMETRIC_ALGS:             # current projects: JWKS
            key = _signing_key(header.get("kid"))
            if key is None:
                raise _unauthorized()
        else:                                    # never trust "none" or anything else
            raise _unauthorized()
        payload = jwt.decode(token, key, algorithms=[alg],
                             audience="authenticated", issuer=ISSUER)
        user_id = str(uuid.UUID(payload.get("sub", "")))
    except (JWTError, ValueError):
        raise _unauthorized() from None

    return {
        "user_id": user_id,
        "email": payload.get("email"),
        "role": payload.get("role", "authenticated"),
        "exp": payload.get("exp"),
    }


async def get_current_user_id(token_data: dict = Depends(validate_supabase_token)) -> str:
    return token_data["user_id"]