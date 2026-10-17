"""Download-once media cache. Fetches via presigned URL, verifies SHA-256,
records the file in SQLite media_cache. Cache hits never touch the network."""
import hashlib
import logging
import os
import tempfile
from pathlib import Path

import requests

from .api_client import get_api_client
from .config import MEDIA_CACHE_DIR
from .database import repository as repo
from .database.models import MediaCache, MediaFile, utcnow
from .database.session import session_scope

logger = logging.getLogger(__name__)
CHUNK = 1024 * 1024


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