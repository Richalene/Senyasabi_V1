"""Section 12 - Performance PT-001 .. PT-007.

Thresholds come from the report and can be overridden with environment variables:
  SENYASABI_STRESS_SECONDS (default 20; set 1800 for the full 30-minute PT-005 run)
  SENYASABI_MAX_RSS_MB     (default 2048; set to your minimum-spec budget for PT-007)
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import textwrap
import time
import tracemalloc
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support  # noqa: E402,F401
from support import APP_ROOT, TempDatabase, new_user, seed_content  # noqa: E402

import numpy as np  # noqa: E402

STARTUP_MAX_S, RECOGNITION_MAX_S, QUERY_MAX_S, MIN_FPS = 10.0, 2.0, 1.0, 15.0
STRESS_SECONDS = float(os.environ.get("SENYASABI_STRESS_SECONDS", "20"))
MAX_RSS_MB = float(os.environ.get("SENYASABI_MAX_RSS_MB", "2048"))


class _StubPreprocessor:
    def process(self, frame):
        return np.zeros(172, np.float32), False, 0

    def draw(self, frame):
        return frame

    def close(self):
        pass


class _FakeCapture:
    def __init__(self):
        self.frame = np.zeros((480, 640, 3), np.uint8)

    def read(self):
        return True, self.frame

    def isOpened(self):
        return True

    def release(self):
        pass


def build_stub_engine():
    """Real CategoryRecognitionEngine/SequenceRecognizer plumbing with a stub detector and model."""
    from backend import word_landmarks as wl
    from backend.model_service import CategoryRecognitionEngine, ModelState, SequenceRecognizer
    cfg = dict(num_frames=24, feature_dim=172, num_hands=2, pose_indices=list(wl.POSE_INDICES),
               feature_order=wl.FEATURE_ORDER, normalization=wl.NORMALIZATION)
    model = Mock(predict=Mock(return_value=np.array([[0.1, 0.9]], np.float32)))
    registry = Mock(get_category_recognizer=Mock(return_value=ModelState(
        "days", True, "", SequenceRecognizer(model, ("MONDAY", "TUESDAY"), cfg))))
    engine = CategoryRecognitionEngine("days", registry=registry,
                                       preprocessor_factory=lambda _cfg: _StubPreprocessor())
    engine._cap = _FakeCapture()
    return engine


class StartupAndLatencyTests(unittest.TestCase):
    def test_pt_001_application_startup_time(self):
        script = textwrap.dedent(f"""
            import os, sys, time
            t = time.perf_counter()
            sys.path.insert(0, r"{APP_ROOT}")
            from backend import initialize_database
            initialize_database()
            from PySide6.QtWidgets import QApplication
            app = QApplication([])
            from screens.app_controller import AppController
            c = AppController(); c.show_welcome(); app.processEvents()
            print("ELAPSED", time.perf_counter() - t, flush=True)
            os._exit(0)
        """)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            env = dict(os.environ, QT_QPA_PLATFORM="offscreen", SENYASABI_DB=str(Path(tmp, "startup.db")))
            run = subprocess.run([sys.executable, "-c", script], cwd=APP_ROOT.parent, env=env,
                                 capture_output=True, text=True, timeout=120)
        line = next((l for l in run.stdout.splitlines() if l.startswith("ELAPSED")), None)
        self.assertIsNotNone(line, run.stdout + run.stderr[-800:])
        elapsed = float(line.split()[1])
        self.assertLessEqual(elapsed, STARTUP_MAX_S, f"start-up took {elapsed:.1f}s")

    def test_pt_002_recognition_pipeline_latency(self):
        engine = build_stub_engine()
        self.addCleanup(engine.close)
        latencies, predicted = [], False
        for _ in range(60):
            t = time.perf_counter()
            result = engine.read_frame()
            latencies.append(time.perf_counter() - t)
            predicted = predicted or (result is not None and result.prediction is not None)
        self.assertTrue(predicted)
        self.assertLessEqual(max(latencies), RECOGNITION_MAX_S)

    @unittest.skipUnless(importlib.util.find_spec("tensorflow"), "tensorflow not installed")
    def test_pt_002_real_alphabet_model_latency(self):
        from backend import config
        if not Path(config.ALPHABET_MODEL_PATH).is_file():
            self.skipTest("alphabet.keras not installed")
        from backend.recognition_engine import SignPredictor
        scaler = config.ALPHABET_SCALER_PATH if Path(config.ALPHABET_SCALER_PATH).is_file() else None
        predictor = SignPredictor(config.ALPHABET_MODEL_PATH,
                                  labels_fallback=config.ALPHABET_LABELS_FALLBACK, scaler_path=scaler)
        features = np.random.default_rng(0).normal(size=63)
        predictor.predict(features)                                    # warm-up / graph tracing
        times = []
        for _ in range(20):
            t = time.perf_counter()
            predictor.predict(features)
            times.append(time.perf_counter() - t)
        self.assertLessEqual(max(times), RECOGNITION_MAX_S)

    @unittest.skipUnless(importlib.util.find_spec("tensorflow"), "tensorflow not installed")
    def test_pt_002_real_word_models_latency(self):
        from backend.model_service import MODEL_ROOT, get_category_recognizer
        base = Path(MODEL_ROOT) / "word_categories"
        codes = [p.name for p in base.iterdir() if p.is_dir()] if base.is_dir() else []
        checked = 0
        for code in codes:
            state = get_category_recognizer(code)
            if not state.available:
                continue
            rec = state.recognizer.fork()
            rng = np.random.default_rng(1)
            for _ in range(25):
                rec.predict_frame(rng.normal(size=172).astype(np.float32))
            t = time.perf_counter()
            rec.predict_frame(rng.normal(size=172).astype(np.float32))
            self.assertLessEqual(time.perf_counter() - t, RECOGNITION_MAX_S, code)
            checked += 1
        if not checked:
            self.skipTest("no category model installed")


class DatabasePerformanceTests(unittest.TestCase):
    def setUp(self):
        from backend.database import models as m
        self.m = m
        self.db = TempDatabase()
        self.addCleanup(self.db.close)
        now = datetime.now(timezone.utc)
        with self.db.scope() as s:
            seed_content(s)
            self.uid = new_user(s)
            s.add_all([m.QuizAttempt(attempt_id=uuid.uuid4(), user_id=self.uid, quiz_id=1, started_at=now,
                                     completed_at=now, score=8, max_score=10, percentage=80.0, passed=True,
                                     duration_seconds=60, camera_accuracy=70.0, mc_accuracy=90.0)
                       for _ in range(500)])
            s.add_all([m.MinigameAttempt(game_attempt_id=uuid.uuid4(), user_id=self.uid, minigame_id=1,
                                         started_at=now, completed_at=now, score=40, duration_seconds=60,
                                         accuracy=75.0) for _ in range(200)])

    def _timed(self, fn):
        t = time.perf_counter()
        fn()
        return time.perf_counter() - t

    def test_pt_003_database_query_speed(self):
        from backend import dashboard_service
        from backend.database import repository as repo
        from sqlalchemy import text
        with patch("backend.dashboard_service.session_scope", self.db.scope):
            dash = self._timed(lambda: dashboard_service.SQLiteDashboardRepository()
                               .get_dashboard_stats(self.uid))

        def plain():
            with self.db.scope() as s:
                s.execute(text("SELECT count(*) FROM quiz_attempts WHERE user_id = :u"),
                          {"u": self.uid.hex}).scalar()
                repo.list_leaderboard_cache(s, "all_time", 100)
        self.assertLessEqual(dash, QUERY_MAX_S, f"dashboard aggregate {dash:.2f}s")
        self.assertLessEqual(self._timed(plain), QUERY_MAX_S)

    def test_pt_004_five_concurrent_sessions(self):
        from backend.database import repository as repo

        def session(n):
            with self.db.scope() as s:
                uid = new_user(s, f"conc{n}")
                now = datetime.now(timezone.utc)
                for _ in range(20):
                    repo.upsert_quiz_attempt(s, uid, uuid.uuid4(), 1, started_at=now, completed_at=now,
                                             score=5, max_score=10, percentage=50.0)
            with self.db.scope() as s:
                return s.query(self.m.QuizAttempt).filter_by(user_id=uid).count()

        t = time.perf_counter()
        with ThreadPoolExecutor(max_workers=5) as pool:
            counts = list(pool.map(session, range(5)))
        self.assertEqual(counts, [20] * 5)
        self.assertLess(time.perf_counter() - t, 30)

    def test_pt_005_continuous_use_is_stable(self):
        from backend.database import repository as repo
        engine = build_stub_engine()
        self.addCleanup(engine.close)
        deadline, frames, baseline = time.perf_counter() + STRESS_SECONDS, 0, None
        tracemalloc.start()
        try:
            while time.perf_counter() < deadline:
                engine.read_frame()
                frames += 1
                if frames == 200:
                    baseline = tracemalloc.get_traced_memory()[0]
                if frames % 100 == 0:
                    now = datetime.now(timezone.utc)
                    with self.db.scope() as s:
                        repo.upsert_quiz_attempt(s, self.uid, uuid.uuid4(), 1, started_at=now,
                                                 completed_at=now, score=1, max_score=2, percentage=50.0)
                self.assertLessEqual(len(engine.recognizer.frames), 24)   # buffer never grows
            growth_mb = (tracemalloc.get_traced_memory()[0] - (baseline or 0)) / 1e6
        finally:
            tracemalloc.stop()
        self.assertGreater(frames, 200, "stress loop did not run long enough")
        self.assertLess(growth_mb, 50, f"memory grew by {growth_mb:.1f} MB over {frames} frames")


class ThroughputTests(unittest.TestCase):
    def test_pt_006_pipeline_frame_rate(self):
        engine = build_stub_engine()
        self.addCleanup(engine.close)
        frames, start = 0, time.perf_counter()
        while time.perf_counter() - start < 3:
            engine.read_frame()
            frames += 1
        fps = frames / (time.perf_counter() - start)
        self.assertGreaterEqual(fps, MIN_FPS, f"{fps:.1f} FPS")

    def test_pt_006_real_mediapipe_hands_frame_rate(self):
        try:
            import mediapipe as mp
            mp.solutions.hands
            from backend.recognition_engine import HandLandmarkExtractor
        except Exception as error:
            self.skipTest(f"mediapipe unavailable: {error}")
        extractor = HandLandmarkExtractor()
        self.addCleanup(extractor.close)
        frame = np.zeros((480, 640, 3), np.uint8)
        extractor.process(frame)                                       # warm-up
        frames, start = 0, time.perf_counter()
        while time.perf_counter() - start < 3:
            extractor.process(frame)
            frames += 1
        self.assertGreaterEqual(frames / (time.perf_counter() - start), MIN_FPS)

    @unittest.skipUnless(importlib.util.find_spec("psutil"), "psutil not installed")
    def test_pt_007_cpu_and_ram_budget(self):
        import psutil
        engine = build_stub_engine()
        self.addCleanup(engine.close)
        for _ in range(500):
            engine.read_frame()
        proc = psutil.Process()
        rss_mb = proc.memory_info().rss / 1e6
        self.assertLessEqual(rss_mb, MAX_RSS_MB, f"RSS {rss_mb:.0f} MB")
        self.assertLessEqual(proc.num_threads(), 64)


if __name__ == "__main__":
    unittest.main()