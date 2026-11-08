"""Download-once media cache. Fetches via presigned URL, verifies SHA-256,
records the file in SQLite media_cache. Cache hits never touch the network."""
from dataclasses import dataclass, replace
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import tempfile
from typing import Protocol
import threading

import requests

from .api_client import get_api_client
from .config import MEDIA_CACHE_DIR, CLIENT_MODE
from .content_service import ROOT, get_sign
from .database import repository as repo
from .database.models import MediaCache, MediaFile, utcnow
from .database.session import session_scope
from .database.models import LessonMedia

log = logging.getLogger(__name__)
logger = log
VIDEO_ROOT = ROOT / "resources/videos"
CHUNK = 1024 * 1024
_STILLS = {}                      # 'A' -> Path, filled from lesson_media of the alphabet lessons
_stills_lock = threading.Lock()
_warming = False
_BUNDLED = ROOT / "resources/VRM_SIGNS"

NUMBER_WORD_MAP = {
    "1": "one", "2": "two", "3": "three", "4": "four", "5": "five",
    "6": "six", "7": "seven", "8": "eight", "9": "nine", "10": "ten",
}
WORD_TO_NUMBER_MAP = {v: k for k, v in NUMBER_WORD_MAP.items()}

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
        clean_code = str(sign_code).strip().casefold() if sign_code is not None else ""
        sign = get_sign(module_code, sign_code)
        if sign is None and clean_code:
            if clean_code in WORD_TO_NUMBER_MAP:
                sign = get_sign(module_code, WORD_TO_NUMBER_MAP[clean_code])
            elif clean_code in NUMBER_WORD_MAP:
                sign = get_sign(module_code, NUMBER_WORD_MAP[clean_code])
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

        candidate_modules = []
        if module_code and str(module_code).casefold() not in ("communication", "basic_communication"):
            candidate_modules.append(str(module_code).casefold())
        if sign.module_code:
            sm = str(sign.module_code).casefold()
            if sm not in candidate_modules:
                candidate_modules.append(sm)
        if any(m in ("communication", "basic_communication") for m in (str(module_code).casefold(), str(sign.module_code).casefold())):
            for sub in ("greeting", "survival"):
                if sub not in candidate_modules:
                    candidate_modules.append(sub)

        candidate_sign_codes = []
        for sc in (sign_code, getattr(sign, "sign_code", None), getattr(sign, "label", None), getattr(sign, "recognition_label", None)):
            if not sc:
                continue
            sc_clean = str(sc).strip().casefold()
            sc_snake = sc_clean.replace(" ", "_").replace("-", "_")
            for v in (sc_clean, sc_snake):
                if v and v not in candidate_sign_codes:
                    candidate_sign_codes.append(v)
                if v in NUMBER_WORD_MAP:
                    w = NUMBER_WORD_MAP[v]
                    if w not in candidate_sign_codes:
                        candidate_sign_codes.append(w)
                elif v in WORD_TO_NUMBER_MAP:
                    n = WORD_TO_NUMBER_MAP[v]
                    if n not in candidate_sign_codes:
                        candidate_sign_codes.append(n)

        # Optional manifest maps stable sign codes to arbitrary relative filenames.
        manifest = self.root / "media_manifest.json"
        relative = None
        if manifest.is_file():
            try:
                manifest_data = json.loads(manifest.read_text(encoding="utf-8-sig"))
                if not isinstance(manifest_data, dict):
                    raise ValueError("Manifest content must be a JSON object")

                def _norm(k):
                    return re.sub(r"[^a-z0-9]+", "", str(k).casefold())

                clean_candidates = {_norm(sc) for sc in candidate_sign_codes if _norm(sc)}

                for mod in candidate_modules:
                    mod_section = manifest_data.get(mod)
                    if not isinstance(mod_section, dict):
                        continue
                    for sc in candidate_sign_codes:
                        rel = mod_section.get(sc)
                        if rel is not None:
                            if not isinstance(rel, str):
                                raise ValueError("Media paths must be strings")
                            relative = rel
                            break
                    if relative:
                        break
                    for m_key, rel in mod_section.items():
                        if _norm(m_key) in clean_candidates:
                            if not isinstance(rel, str):
                                raise ValueError("Media paths must be strings")
                            relative = rel
                            break
                    if relative:
                        break
            except (OSError, ValueError, TypeError, AttributeError) as error:
                log.warning("Invalid media manifest %s: %s", manifest, error)
                relative = None

        if relative:
            candidates = [(self.root / relative).resolve()]
        else:
            candidates = [
                (self.root / ("alphabet" if mod == "alphabet" else f"word_categories/{mod}") / f"{sc}{extension}").resolve()
                for mod in candidate_modules
                for sc in candidate_sign_codes
                for extension in (".mp4", ".webm", ".mov", ".m4v")
            ]

        for path in candidates:
            if path.is_relative_to(self.root) and path.is_file():
                return replace(record, local_path=path, status="bundled", message="")
        # Remote metadata is retained for a future cache adapter. No UI network fetch.
        return replace(record, local_path=None, status="unavailable")


_service = MediaService()

def get_lesson_media(lesson_id, role=None) -> dict[str, int]:
    """{'A': media_id, ...} for a lesson's images in the local cache, keyed by filename stem."""
    from sqlalchemy import select
    query = (select(MediaFile.file_name, LessonMedia.media_id)
             .join(MediaFile, MediaFile.media_id == LessonMedia.media_id)
             .where(LessonMedia.lesson_id == lesson_id, LessonMedia.is_deleted.is_(False),
                    MediaFile.is_deleted.is_(False), MediaFile.media_type == "Image")
             .order_by(LessonMedia.display_order))
    if role:
        query = query.where(LessonMedia.media_role == role)
    with session_scope() as db:
        return {Path(name or "").stem.upper(): media_id for name, media_id in db.execute(query)}


def fetch_lesson_images(lesson_id, role=None) -> dict[str, Path]:
    """{'A': local Path}. Blocking (may download): call from a worker thread."""
    paths = {}
    for key, media_id in get_lesson_media(lesson_id, role).items():
        path = get_media_path(media_id)
        if path is not None:
            paths[key] = path
    return paths

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
    info = get_api_client()._request("GET", f"/api/v1/media/presign/{media_id}")
    
    if not info or not info.get("url"):
        return None                              # offline / not found

    MEDIA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{media_id}_{Path(info.get('file_name') or 'media').name}"
    dest = MEDIA_CACHE_DIR / name
    sha = hashlib.sha256()

    fd, tmp_name = tempfile.mkstemp(dir=MEDIA_CACHE_DIR, suffix=".part")
    try:
        logger.info(
            "Downloading media_id=%s, file_name=%s, url=%s",
            media_id,
            info.get("file_name"),
            info.get("url"),
        )
        with os.fdopen(fd, "wb") as f, requests.get(info["url"], stream=True, timeout=30) as r:
            if not r.ok:
                logger.error(
                    "Media download failed: id=%s, status=%s, "
                    "url=%s, response=%s",
                    media_id,
                    r.status_code,
                    r.url,
                    r.text[:1000],
                )
            r.raise_for_status()

            for chunk in r.iter_content(CHUNK):
                if chunk:
                    f.write(chunk)
                    sha.update(chunk)

        expected = info.get("checksum_sha256")
        if expected and sha.hexdigest() != expected:
            raise ValueError("checksum mismatch")
        
        os.replace(tmp_name, dest)               # atomic: never a half-written file
        logger.info(
            "Successfully downloaded and verified media_id=%s, file_name=%s, destination=%s",
            media_id,
            info.get("file_name"),
            dest,
        )
    except Exception:
        logger.exception("Media download failed for %s", media_id)
        Path(tmp_name).unlink(missing_ok=True)
        return None

    digest = sha.digest()
    with session_scope() as db:
        version = repo.get_content_version_by_number(db, info["content_version_number"])
        if version is None:
            logger.warning("Content version %s missing locally", info["content_version_number"])
            return dest  # file is usable; skip DB record
        
        cv_id = version.content_version_id

        # 1. Ensure the media_files row exists without overwriting its real object_key
        media_record = db.get(MediaFile, media_id)
        if media_record is None:
            # Fallback only if the sync missed it; otherwise, let server snapshot provide the key
            db.add(MediaFile(
                media_id=media_id,
                file_name=info.get("file_name"),
                object_key=info.get("object_key"),  # Use real key from info if available
                media_type=info["media_type"],
                width=info.get("width"),
                height=info.get("height"),
                duration_seconds=info.get("duration_seconds"),
                file_size=info.get("file_size"),
                checksum=digest,
                content_version_id=cv_id
            ))
            db.flush()

        # 2. Record only local cache metadata in MediaCache (local_path vs remote storage)
        db.merge(MediaCache(
            media_id=media_id,
            local_path=name,                  # Local disk path
            content_version_id=cv_id,
            checksum=digest,
            cached_at=utcnow()
        ))
    return dest


def _get_media_info_supabase(media_id: int) -> dict | None:
    """Get media info and signed URL from Supabase Storage (distributed mode)."""
    try:
        from .supabase_client import get_supabase_client
        from .database.session import session_scope
        from .database import repository as repo
        from .config import SUPABASE_URL
        from urllib.parse import quote

        if not SUPABASE_URL:
            return None
        
        supabase = get_supabase_client()
        
        # Get media metadata from database
        with session_scope() as db:
            media = db.get(MediaFile, media_id)
            if media is None or media.is_deleted:
                return None
            
            object_key = media.object_key
            file_name = media.file_name
            media_type = media.media_type
            width = media.width
            height = media.height
            duration = media.duration_seconds
            file_size = media.file_size
            content_version = repo.get_content_version(db, media.content_version_id)
        
        if not content_version:
            return None
        
        storage_url = (
            f"{SUPABASE_URL.rstrip('/')}"
            f"/storage/v1/object/public/senyasabi-media/"
            f"{quote(object_key, safe='/')}"
        )

        return {
            "url": storage_url,
            "file_name": file_name,
            "media_type": media_type,
            "width": width,
            "height": height,
            "duration_seconds": duration,
            "file_size": file_size,
            "checksum_sha256": getattr(content_version, "checksum_sha256", None),
            "content_version_number": content_version.version_number,
        }
        
    except Exception as e:
        logger.warning("Failed to get media info from Supabase: %s", e)
        return None

def load_alphabet_stills(download=False) -> int:
    """Fill the in-memory letter map from lesson_media. download=False only reads files that are
    already cached (fast, UI-safe); download=True fetches missing ones (blocking: worker thread)."""
    from .content_service import get_synced_lessons
    found = {}
    for lesson in get_synced_lessons("alphabet"):
        if lesson["lesson_id"] is None:
            continue
        for key, media_id in get_lesson_media(lesson["lesson_id"]).items():
            path = get_media_path(media_id) if download else _cached_path(media_id)
            if path is not None:
                found[key] = path
    with _stills_lock:
        _STILLS.update(found)
    return len(found)


def alphabet_still(letter):
    """Path for a letter's image: Supabase-cached copy, else the bundled PNG, else None.
    Memory lookup only, safe to call from paint code."""
    key = str(letter).upper()
    with _stills_lock:
        path = _STILLS.get(key)
    if path is not None and path.is_file():
        return path
    bundled = _BUNDLED / f"{key}.png"
    return bundled if bundled.is_file() else None


def warm_alphabet_stills():
    """Load cached images now, then download the rest in the background. Never raises."""
    global _warming
    try:
        load_alphabet_stills(download=False)
    except Exception as error:
        log.warning("Alphabet image cache unavailable: %s", error)
    with _stills_lock:
        if _warming:
            return
        _warming = True

    def work():
        global _warming
        try:
            load_alphabet_stills(download=True)
        except Exception as error:
            log.warning("Alphabet image download failed: %s", error)
        finally:
            with _stills_lock:
                _warming = False

    threading.Thread(target=work, name="alphabet-stills", daemon=True).start()