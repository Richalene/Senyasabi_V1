"""Section 8 - Functional test cases TC-F-001 .. TC-F-016."""
import sys
import unittest
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support  # noqa: E402,F401
from support import APP_ROOT, OfflineAuthCase, TempDatabase, new_user, seed_content, qt_app  # noqa: E402

import numpy as np  # noqa: E402


class AuthFunctionalTests(OfflineAuthCase):
    def test_tc_f_001_login_valid_credentials(self):
        self.auth.register_user("mary", "mary@example.com", "SecretPass123", "Mary")
        user = self.auth.authenticate_user("mary", "SecretPass123")
        self.assertEqual(user["username"], "mary")
        self.assertEqual(self.auth.get_current_user()["username"], "mary")
        self.assertNotIn("password_hash", user)

    def test_tc_f_002_login_invalid_password(self):
        self.auth.register_user("mary", "mary@example.com", "SecretPass123", "Mary")
        with self.assertRaises(self.auth.AuthError):
            self.auth.authenticate_user("mary", "WrongPassword!")
        self.assertIsNone(self.auth.get_current_user())

    def test_tc_f_003_registration_valid(self):
        result = self.auth.register_user("newlearner", "new@example.com", "SecretPass123", "New Learner")
        self.assertEqual(result["username"], "newlearner")
        self.assertEqual(result["email"], "new@example.com")
        self.assertNotIn("password", result)
        self.assertIsNotNone(self.auth._repository.find_by_identifier("newlearner"))
        self.assertIsNotNone(self.auth._repository.find_by_identifier("new@example.com"))


class DashboardFunctionalTests(unittest.TestCase):
    def test_tc_f_004_dashboard_data_has_every_area(self):
        from backend import dashboard_service
        raw = dashboard_service.get_dashboard_stats(None)
        dash = dashboard_service.build_dashboard(raw)
        for key in ("leaderboard_rank", "latest_badge", "current_module",
                    "lessons_completed", "minigames_completed", "radar"):
            self.assertIn(key, dash)
        self.assertEqual(dash["lessons_completed"], 0)

    def test_tc_f_004_dashboard_window_renders_all_areas(self):
        qt_app()
        from backend import dashboard_service
        from screens.dashboard.dashboard import DashboardWindow
        window = DashboardWindow()
        try:
            window._render_home_stats(
                dashboard_service.DefaultDashboardRepository().get_dashboard_stats(None))
            ui = window.ui
            for name in ("btnStartLearning", "btnMinigames", "btnLessonsCompleted",
                         "btnModule", "btnLatestBadge", "btnLeaderboardRank"):
                self.assertIsNotNone(getattr(ui, name), name)
            self.assertEqual(ui.lblLessonsCompleted.text(), "0")
            self.assertEqual(ui.lblLeaderboardRank.text(), "Unranked")
            self.assertEqual(ui.streakValue.text(), "0 Days")
        finally:
            window.close()
            window.deleteLater()


class LessonFunctionalTests(unittest.TestCase):
    def test_tc_f_005_select_lesson_by_level(self):
        from backend import content_service as cs
        lessons = cs.get_lessons_for_module("alphabet")
        self.assertEqual(len(lessons), 4)
        self.assertEqual([l.order for l in lessons], [1, 2, 3, 4])
        self.assertEqual([s.label for s in cs.get_signs_for_lesson("alphabet", 2)], list("GHIJKL"))
        self.assertEqual(len(cs.get_signs_for_lesson("number", 1)), 5)
        with self.assertRaises(ValueError):
            cs.get_signs_for_lesson("alphabet", 99)

    def test_tc_f_006_demonstrator_media_for_every_letter(self):
        from backend.media_service import alphabet_still, resolve_sign_video
        vrm = APP_ROOT / "resources" / "VRM_SIGNS"
        if not vrm.is_dir():
            self.skipTest("resources/VRM_SIGNS is not installed")
        missing = [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if alphabet_still(c) is None]
        self.assertEqual(missing, [], f"No demonstration image for: {missing}")
        record = resolve_sign_video("days", "monday")      # must resolve without raising
        if record.available:
            self.assertTrue(record.local_path.is_file())


class RecognitionFunctionalTests(unittest.TestCase):
    def _session(self, targets, **kw):
        from backend.session_state import CameraPracticeSession
        return CameraPracticeSession(targets=targets, confidence_threshold=0.7,
                                     hold_frames=3, grace_frames=2, **kw)

    def test_tc_f_007_correct_sign_scores_and_gives_feedback(self):
        from backend.session_state import Event, SessionState
        s = self._session(["A", "B"])
        events = [s.process_prediction("A", 0.95) for _ in range(3)]
        self.assertEqual(events, [Event.HOLDING, Event.HOLDING, Event.CORRECT])
        self.assertEqual(s.score, 1)
        self.assertIs(s.state, SessionState.FEEDBACK)
        s.advance()
        self.assertEqual(s.current_target, "B")
        for _ in range(3):
            s.process_prediction("B", 0.95)
        s.advance()
        self.assertTrue(s.is_done())
        self.assertEqual(s.score_percent(), 100)
        self.assertGreaterEqual(s.accuracy_percent(), 90)

    def test_tc_f_008_incorrect_sign_is_not_credited(self):
        from backend.session_state import Event
        s = self._session(["A"])
        for _ in range(30):
            self.assertIsNot(s.process_prediction("B", 0.99), Event.CORRECT)   # wrong sign
            self.assertIsNot(s.process_prediction("A", 0.20), Event.CORRECT)   # right sign, low confidence
        self.assertEqual(s.score, 0)
        self.assertFalse(s.is_done())

    def test_tc_f_009_no_hand_in_view(self):
        from backend.recognition_engine import SignRecognitionEngine
        frame = np.zeros((480, 640, 3), np.uint8)
        engine = SignRecognitionEngine.__new__(SignRecognitionEngine)
        engine._cap = Mock(read=Mock(return_value=(True, frame)))
        engine.extractor = Mock(process=Mock(return_value=(None, Mock())),
                                draw=Mock(return_value=frame))
        engine.predictor = Mock()
        result = engine.read_frame()
        self.assertFalse(result.hand_detected)
        self.assertIsNone(result.prediction)
        engine.predictor.predict.assert_not_called()


class MinigameFunctionalTests(unittest.TestCase):
    def _play(self, kind):
        from backend.minigame_service import GameSession
        clock = Mock(return_value=100.0)
        g = GameSession(kind, rounds=3, module_code="days", clock=clock)
        self.assertEqual(g.total, 3)
        while not g.complete:
            self.assertFalse(g.check_answer("definitely wrong"))
            self.assertTrue(g.check_answer(g.word))
            self.assertTrue(g.finish(True))
            g.next_round()
        self.assertEqual(g.score, 3)
        # an answer that arrives after the timer expired earns no point
        late = GameSession(kind, rounds=2, module_code="days", clock=clock)
        clock.return_value += 10_000
        late.finish(True)
        self.assertEqual(late.score, 0)

    def test_tc_f_010_sign_sprint_full_round(self):
        self._play("sprint")

    def test_tc_f_011_fingerspell_quest_full_round(self):
        self._play("quest")

    def test_tc_f_012_sign_detective_full_round(self):
        self._play("detective")


class ProgressFunctionalTests(unittest.TestCase):
    def setUp(self):
        self.db = TempDatabase()
        self.addCleanup(self.db.close)
        with self.db.scope() as s:
            cv = seed_content(s)
            from backend.database import repository as repo
            repo.create_module(s, 2, "number", "Numbers", cv, 2)
            repo.create_lesson(s, 2, "number_lesson_1", "One to Five", cv, 2, 1)
            self.uid = new_user(s)

    def test_tc_f_013_completing_a_lesson_saves_and_advances(self):
        from backend.database import repository as repo
        with self.db.scope() as s:
            self.assertEqual(repo.get_current_module(s, self.uid).module_code, "alphabet")
            progress = repo.create_or_update_lesson_progress(
                s, self.uid, 1, 100.0, "Completed", time_spent_seconds=60)
            self.assertIsNotNone(progress.completed_at)
        self.db.reopen()
        with self.db.scope() as s:
            saved = repo.get_lesson_progress(s, self.uid, 1)
            self.assertEqual(saved.status, "Completed")
            # the app has no hard lock; "unlocking" = the learning pointer moves on
            self.assertEqual(repo.get_current_module(s, self.uid).module_code, "number")

    def test_tc_f_014_statistics_match_learner_data(self):
        from backend import dashboard_service
        from backend.database import repository as repo
        now = datetime.now(timezone.utc)
        with self.db.scope() as s:
            repo.create_or_update_lesson_progress(s, self.uid, 1, 100.0, "Completed", time_spent_seconds=60)
            repo.upsert_quiz_attempt(s, user_id=self.uid, attempt_id=uuid.uuid4(), quiz_id=1,
                                     started_at=now - timedelta(minutes=2), completed_at=now,
                                     score=8, max_score=10, percentage=80.0, passed=True,
                                     duration_seconds=120, camera_accuracy=70.0, mc_accuracy=90.0)
            repo.upsert_minigame_attempt(s, self.uid, uuid.uuid4(), 1, now - timedelta(minutes=1),
                                         now, 40, 60, 75.0)
            s.commit()
            repo.rebuild_user_statistics(s, self.uid)
        with patch("backend.dashboard_service.session_scope", self.db.scope):
            data = dashboard_service.SQLiteDashboardRepository().get_dashboard_stats(self.uid)
        stats = data["user_statistics"]
        self.assertEqual((stats["lessons_completed"], stats["quizzes_completed"],
                          stats["minigames_completed"]), (1, 1, 1))
        self.assertEqual((stats["total_quiz_score"], stats["total_minigame_score"]), (8, 40))
        self.assertEqual(data["module_performance"][0]["score"], 75.0)   # 0.5*80 + 0.5*70

    @unittest.skip("TC-F-015: in-app store is not implemented yet")
    def test_tc_f_015_spend_points_in_store(self):
        pass

    def test_tc_f_016_save_and_retrieve_activity_records(self):
        from backend.database import repository as repo
        attempt_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        with self.db.scope() as s:
            repo.upsert_quiz_attempt(s, user_id=self.uid, attempt_id=attempt_id, quiz_id=1,
                                     started_at=now, completed_at=now, score=9, max_score=10,
                                     percentage=90.0, passed=True)
            repo.enqueue_sync(s, uuid.uuid4(), self.uid, "quiz_attempt", attempt_id, {"score": 9})
        with self.db.scope() as s:
            from backend.database import models as m
            row = s.get(m.QuizAttempt, attempt_id)
            self.assertEqual((row.score, row.passed), (9, True))
            pending = repo.dequeue_pending_sync(s, user_id=self.uid)
            self.assertEqual(len(pending), 1)
            repo.mark_synced(s, pending[0].sync_id)
            self.assertEqual(repo.dequeue_pending_sync(s, user_id=self.uid), [])


if __name__ == "__main__":
    unittest.main()
