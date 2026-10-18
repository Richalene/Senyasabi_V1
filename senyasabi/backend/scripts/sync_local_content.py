"""
Pull published learning content from Supabase/Postgres into the local SQLite cache.

Content rows are merged by their server-assigned IDs (db.merge), exactly as the
SyncService.sync_content_from_server docstring describes. Only content tables are
touched; local user data, progress, and the sync queue are never modified, and
nothing is deleted. Safe to re-run.

Usage (from senyasabi/):  python -m backend.scripts.sync_local_content
"""
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.pool import NullPool

from backend import config
from backend.database import models as m
from backend.database.session import session_scope

# FK order. Media tables are included so links stay consistent if/when they exist.
TABLES = [m.ContentVersion, m.Module, m.Lesson, m.Sign, m.LessonSign, m.Quiz, m.QuizSign,
          m.Badge, m.Minigame, m.MinigameSign, m.MediaFile, m.SignMedia]


def main():
    if not config.POSTGRESQL_URL:
        sys.exit("ERROR: DATABASE_URL not set")
    pg = create_engine(config.POSTGRESQL_URL, poolclass=NullPool, connect_args={"prepare_threshold": None})
    with pg.connect() as src, session_scope() as dst:
        cv_map = {}  # server content_version_id -> local content_version_id
        for model in TABLES:
            cols = [c.key for c in model.__mapper__.column_attrs]
            rows = src.execute(select(*[getattr(model, c) for c in cols])).all()
            for row in rows:
                data = dict(zip(cols, row))
                if model is m.ContentVersion:
                    local = dst.scalar(select(m.ContentVersion).where(
                        m.ContentVersion.version_number == data["version_number"]))
                    cv_map[data["content_version_id"]] = (
                        local.content_version_id if local else data["content_version_id"])
                    data["content_version_id"] = cv_map[data["content_version_id"]]
                elif "content_version_id" in data:
                    data["content_version_id"] = cv_map.get(
                        data["content_version_id"], data["content_version_id"])
                dst.merge(model(**data))
            dst.flush()
            print(f"  {model.__tablename__}: {len(rows)} merged", flush=True)


if __name__ == "__main__":
    main()
