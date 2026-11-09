"""Media API: metadata + short-lived presigned URLs (Supabase Storage, S3 protocol)."""
from functools import lru_cache

import boto3
from botocore.config import Config
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from ..config import S3_ENDPOINT, S3_REGION, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY
from ..database.postgre_session import get_postgres_session
from ..security import get_current_user_id

router = APIRouter(prefix="/api/v1/media", tags=["media"])

PRESIGN_TTL = 300  # seconds


@lru_cache(maxsize=1)
def _s3():
    if not all([S3_ENDPOINT, S3_REGION, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY]):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Supabase Storage is not configured")
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        region_name=S3_REGION,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        config=Config(s3={"addressing_style": "path"}, signature_version="s3v4"),
    )


def _media_row(media_id: int) -> dict:
    try:
        db = get_postgres_session()
    except RuntimeError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Database not configured")
    with db:
        row = db.execute(text("""
            SELECT m.media_id, m.file_name, m.object_key, m.media_type,
                   m.width, m.height, m.duration_seconds, m.file_size, m.checksum,
                   cv.version_number AS content_version_number
            FROM public.media_files m
            JOIN public.content_versions cv
              ON cv.content_version_id = m.content_version_id
            WHERE m.media_id = :id AND NOT m.is_deleted
        """), {"id": media_id}).mappings().first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Media not found")
    return dict(row)


def _public(row: dict) -> dict:
    """Everything except object_key (clients never need the storage path)."""
    checksum = row["checksum"]
    return {
        "media_id": row["media_id"],
        "file_name": row["file_name"],
        "media_type": row["media_type"],
        "width": row["width"],
        "height": row["height"],
        "duration_seconds": row["duration_seconds"],
        "file_size": row["file_size"],
        "checksum_sha256": bytes(checksum).hex() if checksum else None,
        "content_version_number": row["content_version_number"],
    }


@router.get("/presign/{media_id}")
def get_presigned_url(media_id: int, _user: str = Depends(get_current_user_id)):
    """Metadata plus a short-lived download URL, so the client needs one call."""
    row = _media_row(media_id)
    url = _s3().generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": row["object_key"]},
        ExpiresIn=PRESIGN_TTL,
    )
    return {**_public(row), "url": url, "expires_in": PRESIGN_TTL}


@router.get("/info/{media_id}")
def get_media_info(media_id: int, _user: str = Depends(get_current_user_id)):
    return _public(_media_row(media_id))