"""
FastAPI backend for SenyaSabi.

This provides REST API endpoints for:
- Content synchronization
- Progress tracking
- Media presigned URLs
- Statistics and leaderboard

Authentication is handled via Supabase Auth JWT tokens.
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .config import FASTAPI_HOST, FASTAPI_PORT, FASTAPI_DEBUG, POSTGRESQL_URL
from .security import get_current_user_id
from .api.media import router as media_router
from .api.content import router as content_router
from .api.sync import router as sync_router
from .api.progress import router as progress_router
from .api.leaderboard import router as leaderboard_router
from .api.packages import router as packages_router
from .api.auth import router as auth_router

# Import version from parent package
try:
    from .. import __version__
except ImportError:
    __version__ = "1.0.0"

# Create FastAPI app
app = FastAPI(
    title="SenyaSabi API",
    description="Backend API for SenyaSabi sign language learning app",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(media_router)
app.include_router(content_router)
app.include_router(sync_router)
app.include_router(progress_router)
app.include_router(leaderboard_router)
app.include_router(packages_router)
app.include_router(auth_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "postgres_configured": POSTGRESQL_URL is not None
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "SenyaSabi API",
        "version": __version__,
        "docs": "/docs",
        "status": "PostgreSQL integration in progress"
    }


# Placeholder endpoints (to be implemented)
@app.get("/api/v1/user/profile")
async def get_user_profile(user_id: str = Depends(get_current_user_id)):
    """
    Get user profile.

    This endpoint validates the Supabase JWT token and returns user info from PostgreSQL.
    user_id is a UUID from the JWT sub claim.
    """
    from .database.postgre_session import get_postgres_session
    from sqlalchemy import text

    try:
        with get_postgres_session() as db:
            result = db.execute(text("""
                SELECT user_id::text AS user_id,
                       COALESCE(NULLIF(btrim(display_name), ''), username) AS display_name,
                       username,
                       created_at,
                       updated_at
                FROM public.users
                WHERE user_id = :user_id
            """), {"user_id": user_id}).mappings().first()

            if not result:
                return {
                    "user_id": user_id,
                    "message": "User profile not found in database"
                }

            return dict(result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user profile: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    print(f"Starting SenyaSabi API on {FASTAPI_HOST}:{FASTAPI_PORT}")
    print(f"PostgreSQL configured: {POSTGRESQL_URL is not None}")
    print(f"Debug mode: {FASTAPI_DEBUG}")
    print(f"API docs available at http://{FASTAPI_HOST}:{FASTAPI_PORT}/docs")
    
    uvicorn.run("senyasabi.backend.main:app", host=FASTAPI_HOST, port=FASTAPI_PORT, reload=FASTAPI_DEBUG)
