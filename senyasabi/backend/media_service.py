"""Media resolution and download-once SQLite cache."""
from dataclasses import dataclass, replace
import hashlib
import json
import logging
import os
from pathlib import Path
import tempfile
from typing import Protocol

import requests

from .api_client import get_api_client
from .config import MEDIA_CACHE_DIR, CLIENT_MODE
from .content_service import ROOT, get_sign
from .database import repository as repo
from .database.models import MediaCache, MediaFile, utcnow
from .database.session import session_scope

log = logging.getLogger(__name__)
logger = log
VIDEO_ROOT = ROOT / "resources/videos"
CHUNK = 1024 * 1024


@dataclass(frozen=True)
class MediaRecord:
    module_code: str
    sign_code: str
    media_id: int | None = None
    media_type: str = "video"
    storage_key: str | None = None
    remote_url: str | None = None
    local_cached_path: str | None = None
    version: str | None = None
    checksum: str | None = None
    status: str = "unavailable"
    local_path: Path | None = None
    message: str = "Lesson video is not installed yet."

    @property
    def available(self):
        return self.local_path is not None and self.local_path.is_file()


class MediaRepository(Protocol):
    def get_media_for_sign(self, sign) -> MediaRecord | None: ...


class EmptyMediaRepository:
    def get_media_for_sign(self, sign):
        if getattr(sign, "media_id", None) is not None:
            cached = _cached_path(sign.media_id)
            if cached is not None:
                return MediaRecord(
                    sign.module_code,
                    sign.sign_code,
                    media_id=sign.media_id,
                    local_cached_path=str(cached),
                )
        return None


class MediaService:
    def __init__(self, repository=None, video_root=VIDEO_ROOT):
        self.repository = repository if repository is not None else EmptyMediaRepository()
        self.root = Path(video_root).resolve()

    def resolve_sign_video(self, module_code, sign_code):
        sign = get_sign(module_code, sign_code)
        if sign is None:
            raise ValueError(f"Unknown sign: {module_code}/{sign_code}")
        record = MediaRecord(sign.module_code, sign.sign_code, media_id=sign.media_id)
        try:
            record = self.repository.get_media_for_sign(sign) or record
        except (OSError, ConnectionError, TimeoutError) as error:
            log.warning("Media cache unavailable for %s/%s: %s", module_code, sign_code, error)
        if record.local_cached_path:
            cached = Path(record.local_cached_path)
            if cached.is_file():
                return replace(record, local_path=cached, status="cached", message="")
        folder = self.root / ("alphabet" if sign.module_code == "alphabet"
                              else f"word_categories/{sign.module_code}")
        # Optional manifest maps stable sign codes to arbitrary relative filenames.
        manifest = self.root / "media_manifest.json"
        relative = None
        if manifest.is_file():
            try:
                relative = json.loads(manifest.read_text(encoding="utf-8-sig")).get(
                    sign.module_code, {}).get(sign.sign_code)
                if relative is not None and not isinstance(relative, str):
                    raise ValueError("Media paths must be strings")
            except (OSError, ValueError, TypeError, AttributeError) as error:
                log.warning("Invalid media manifest %s: %s", manifest, error)
                relative = None
        candidates = [(self.root / relative).resolve()] if relative else [
            folder / f"{sign.sign_code}{extension}" for extension in (".mp4", ".webm", ".mov", ".m4v")]
        for path in candidates:
            if path.is_relative_to(self.root) and path.is_file():
                return replace(record, local_path=path, status="bundled", message="")
        # Remote metadata is retained for a future cache adapter. No UI network fetch.
        return replace(record, local_path=None, status="unavailable")


_service = MediaService()


def resolve_sign_video(module_code, sign_code):
    return _service.resolve_sign_video(module_code, sign_code)


def get_media_path(media_id: int) -> Path | None:
    """Local path for a media file, downloading it if needed. None if unavailable.
    Blocking: call from a worker thread, not the Qt UI thread."""
    return _cached_path(media_id) or _download(media_id)


def _cached_path(media_id: int) -> Path | None:
    with session_scope() as db:
        cache = db.get(MediaCache, media_id)
        if cache is None or not cache.local_path:
            return None
        path = MEDIA_CACHE_DIR / cache.local_path
        if not path.is_file():
            return None
        media = db.get(MediaFile, media_id)
        if media is not None:
            if media.file_size and path.stat().st_size != media.file_size:
                return None                      # truncated/corrupt
            if media.checksum and cache.checksum and media.checksum != cache.checksum:
                return None                      # content updated since we cached it
        return path


def _download(media_id: int) -> Path | None:
    # Get media info from appropriate source
    if CLIENT_MODE == "distributed":
        info = _get_media_info_supabase(media_id)
    else:
        info = get_api_client()._request("GET", f"/api/v1/media/presign/{media_id}")
    
    if not info or not info.get("url"):
        return None                              # offline / not found

    MEDIA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{media_id}_{Path(info.get('file_name') or 'media').name}"
    dest = MEDIA_CACHE_DIR / name
    sha = hashlib.sha256()

    fd, tmp_name = tempfile.mkstemp(dir=MEDIA_CACHE_DIR, suffix=".part")
    try:
        with os.fdopen(fd, "wb") as f, requests.get(info["url"], stream=True, timeout=30) as r:
            r.raise_for_status()
            for chunk in r.iter_content(CHUNK):
                f.write(chunk)
                sha.update(chunk)

        expected = info.get("checksum_sha256")
        if expected and sha.hexdigest() != expected:
            raise ValueError("checksum mismatch")
        os.replace(tmp_name, dest)               # atomic: never a half-written file
    except Exception:
        logger.exception("Media download failed for %s", media_id)
        Path(tmp_name).unlink(missing_ok=True)
        return None

    digest = sha.digest()
    with session_scope() as db:
        version = repo.get_content_version_by_number(db, info["content_version_number"])
        if version is None:
            logger.warning("Content version %s missing locally", info["content_version_number"])
            return dest                          # file is usable; skip DB record
        cv_id = version.content_version_id
        # media_cache has an FK to media_files, so make sure the row exists locally.
        db.merge(MediaFile(
            media_id=media_id, file_name=info.get("file_name"),
            object_key=f"media/{media_id}",      # placeholder; real key stays server-side
            media_type=info["media_type"], width=info.get("width"),
            height=info.get("height"), duration_seconds=info.get("duration_seconds"),
            file_size=info.get("file_size"), checksum=digest, content_version_id=cv_id))
        db.flush()
        db.merge(MediaCache(media_id=media_id, local_path=name, content_version_id=cv_id,
                            checksum=digest, cached_at=utcnow()))
    return dest


def _get_media_info_supabase(media_id: int) -> dict | None:
    """Get media info and signed URL from Supabase Storage (distributed mode)."""
    try:
        from .supabase_client import get_supabase_client
        from .database.session import session_scope
        from .database import repository as repo
        from .config import SUPABASE_URL
        
        supabase = get_supabase_client()
        
        # Get media metadata from database
        with session_scope() as db:
            media = db.get(MediaFile, media_id)
            if media is None or media.is_deleted:
                return None
            
            object_key = media.object_key
            file_name = media.file_name
            media_type = media.media_type
            content_version = repo.get_content_version(db, media.content_version_id)
        
        if not content_version:
            return None
        
        # Generate public URL from Supabase Storage
        # Note: For production with private buckets, use signed URLs via Supabase REST API
        # For now, assuming public bucket or using Supabase's default public access
        
        # Construct public URL (assuming bucket is public)
        storage_url = f"{SUPABASE_URL}/storage/v1/object/public/{object_key}"
        
        return {
            "media_id": media_id,
            "file_name": file_name,
            "media_type": media_type,
            "url": storage_url,
            "content_version_number": content_version.version_number,
            "checksum_sha256": media.checksum.hex() if media.checksum else None,
            "width": media.width,
            "height": media.height,
            "duration_seconds": media.duration_seconds,
            "file_size": media.file_size
        }
        
    except Exception as e:
        logger.warning("Failed to get media info from Supabase: %s", e)
        return None
