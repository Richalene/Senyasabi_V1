"""Shared helpers for the evaluation suites. Import this BEFORE any backend module."""
import os
import sqlite3
import sys
import tempfile
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
# Safety net: nothing in the evaluation suites may touch the real local cache.
os.environ.setdefault("SENYASABI_DB", str(Path(tempfile.gettempdir()) / "senyasabi_eval_default.db"))

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

SCHEMA = APP_ROOT / "backend" / "database" / "sqlite_schema.sql"


class TempDatabase:
    """Disposable SQLite DB built from the real schema, FK enforcement + WAL like production."""

    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._tmp.name) / "eval.db"
        conn = sqlite3.connect(self.path)
        try:
            conn.executescript(SCHEMA.read_text(encoding="utf-8"))
            conn.commit()
        finally:
            conn.close()
        self._open()

    def _open(self):
        self.engine = create_engine(f"sqlite:///{self.path.as_posix()}",
                                    connect_args={"timeout": 30})

        @event.listens_for(self.engine, "connect")
        def _pragmas(dbapi, _record):
            cur = dbapi.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False, autoflush=False)

    def reopen(self):
        """Simulate an application restart: drop every connection, reconnect to the same file."""
        self.engine.dispose()
        self._open()

    @contextmanager
    def scope(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self):
        self.engine.dispose()
        self._tmp.cleanup()


def seed_content(db):
    """One content version, module, lesson, quiz, minigame and badge. Returns content_version_id."""
    from backend.database import repository as repo
    cv = repo.create_content_version(db, 1, "evaluation", True).content_version_id
    repo.create_module(db, 1, "alphabet", "Alphabet", cv, 1)
    repo.create_lesson(db, 1, "alphabet_lesson_1", "Letters A - F", cv, 1, 1)
    repo.create_quiz(db, 1, "alphabet_quiz", 1, cv, "Alphabet Quiz")
    repo.create_minigame(db, 1, "sign_sprint", 1, cv, "Sign Sprint", "camera", config={"rounds": 5})
    repo.create_badge(db, 1, "FIRST_STEPS", "First Steps", "Complete a lesson")
    return cv


def new_user(db, name="mary"):
    from backend.database import repository as repo
    uid = uuid.uuid4()
    repo.upsert_user(db, uid, f"{name}_{uid.hex[:6]}", f"{uid.hex[:8]}@example.com", "Mary")
    db.commit()
    return uid


class OfflineAuthCase(unittest.TestCase):
    """auth_service backed by a temp SQLite DB with the network forced offline."""

    def setUp(self):
        from backend import auth_service
        self.auth = auth_service
        self.db = TempDatabase()
        self._saved_repo = auth_service._repository
        auth_service._repository = auth_service.SQLiteUserRepository()
        offline = auth_service.NetworkError("offline")
        for name in ("register", "login", "refresh"):
            p = patch.object(auth_service.auth_client, name, side_effect=offline)
            p.start()
            self.addCleanup(p.stop)
        p = patch.object(auth_service, "session_scope", self.db.scope)
        p.start()
        self.addCleanup(p.stop)
        p = patch.object(auth_service, "get_credential_store")
        self.store = p.start()
        self.store.return_value.get_refresh_token.return_value = None
        self.addCleanup(p.stop)
        auth_service.logout_user()
        self.addCleanup(self._restore)

    def _restore(self):
        self.auth.logout_user()
        self.auth._repository = self._saved_repo
        self.db.close()


def qt_app():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])