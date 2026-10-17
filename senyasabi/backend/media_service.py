"""Resolve media references without coupling Qt to storage, SQLAlchemy or Supabase."""
from dataclasses import dataclass, replace
import json
import logging
from pathlib import Path
from typing import Protocol

from .content_service import ROOT, get_sign

log = logging.getLogger(__name__)
VIDEO_ROOT = ROOT / "resources/videos"


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
