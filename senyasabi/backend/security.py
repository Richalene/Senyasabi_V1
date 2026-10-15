"""Security utilities for FastAPI backend - JWT validation from Supabase Auth."""
import os
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import SUPABASE_URL, SUPABASE_KEY

# HTTP Bearer scheme for token extraction
security = HTTPBearer()

# JWT configuration (Supabase uses RS256)
ALGORITHM = "RS256"
# Supabase JWT issuer
ISSUER = f"{SUPABASE_URL}/auth/v1" if SUPABASE_URL else "https://supabase.com/auth/v1"

# Get JWT secret from Supabase (use service role key for server-side validation)
JWT_SECRET = SUPABASE_KEY if SUPABASE_KEY else os.getenv("SUPABASE_JWT_SECRET")


async def validate_supabase_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Validate Supabase JWT access token and extract user info.
    
    Args:
        credentials: HTTP Bearer credentials containing the JWT token
        
    Returns:
        Dict containing user_id (UUID) and other claims
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        # Decode and validate the JWT
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            options={"verify_aud": False}  # Supabase doesn't require audience validation
        )
        
        # Extract user ID from 'sub' claim (this is the UUID that matches users.user_id)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )
        
        # Check if token is an access token (not refresh token)
        if payload.get("typ") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type: expected access token"
            )
        
        return {
            "user_id": user_id,  # This is the UUID (user_id in users table)
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated"),
            "exp": payload.get("exp")
        }
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


async def get_current_user_id(token_data: dict = Depends(validate_supabase_token)) -> str:
    """
    Extract user_id (UUID) from validated token.
    
    This is used as a dependency in API endpoints to get the user ID.
    No database lookup needed - user_id comes directly from JWT sub claim.
    
    Args:
        token_data: Validated token data from validate_supabase_token
        
    Returns:
        The user_id (UUID string)
    """
    return token_data["user_id"]
