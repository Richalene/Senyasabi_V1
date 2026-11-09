"""Focused regression tests for leaderboard fallback in distributed and direct modes."""
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[2]
_BACKEND = _ROOT / "senyasabi"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from backend.api_client import APIClient, get_api_client
from backend import leaderboard_service


class TestLeaderboardFallback(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    # -------------------------------------------------------------------------
    # Mode-based routing tests
    # -------------------------------------------------------------------------
    @patch.object(APIClient, "_request", return_value=None)
    @patch.object(APIClient, "_get_leaderboard_from_supabase")
    def test_distributed_mode_falls_back_to_supabase_when_fastapi_fails(
        self, mock_supabase, mock_request
    ):
        """In distributed mode, if FastAPI request fails (returns None), queries Supabase."""
        mock_supabase.return_value = {
            "board_code": "all_time",
            "limit": 100,
            "entries": [
                {
                    "user_id": "u-1",
                    "display_name": "Learner One",
                    "total_score": 100,
                    "rank_position": 1,
                    "current_streak": 3,
                    "badge_count": 2,
                }
            ],
            "cached": True,
        }

        with patch("backend.api_client._current_client_mode", return_value="distributed"):
            res = self.client.get_leaderboard("all_time", 100)
            mock_request.assert_called_once()
            mock_supabase.assert_called_once_with("all_time", 100)
            self.assertIsNotNone(res)
            self.assertEqual(len(res["entries"]), 1)
            self.assertEqual(res["entries"][0]["display_name"], "Learner One")

    @patch.object(APIClient, "_request")
    @patch.object(APIClient, "_get_leaderboard_from_supabase")
    def test_distributed_mode_uses_fastapi_when_online(
        self, mock_supabase, mock_request
    ):
        """In distributed mode, if FastAPI succeeds, direct Supabase is NOT queried."""
        fastapi_payload = {
            "board_code": "all_time",
            "limit": 100,
            "entries": [{"user_id": "u-1", "display_name": "API User", "total_score": 200, "rank_position": 1}],
        }
        mock_request.return_value = fastapi_payload

        with patch("backend.api_client._current_client_mode", return_value="distributed"):
            res = self.client.get_leaderboard("all_time", 100)
            mock_request.assert_called_once()
            mock_supabase.assert_not_called()
            self.assertEqual(res, fastapi_payload)

    @patch.object(APIClient, "_request")
    @patch.object(APIClient, "_get_leaderboard_from_supabase")
    def test_direct_mode_calls_supabase_directly(
        self, mock_supabase, mock_request
    ):
        """In direct mode, Supabase is queried directly without calling FastAPI."""
        mock_supabase.return_value = {"board_code": "all_time", "entries": []}

        with patch("backend.api_client._current_client_mode", return_value="direct"):
            res = self.client.get_leaderboard("all_time", 50)
            mock_request.assert_not_called()
            mock_supabase.assert_called_once_with("all_time", 50)
            self.assertEqual(res, {"board_code": "all_time", "entries": []})

    @patch.object(APIClient, "_request")
    @patch.object(APIClient, "_get_leaderboard_from_supabase")
    def test_fastapi_mode_queries_fastapi_only(
        self, mock_supabase, mock_request
    ):
        """In fastapi mode, only FastAPI is queried, never Supabase."""
        mock_request.return_value = None

        with patch("backend.api_client._current_client_mode", return_value="fastapi"):
            res = self.client.get_leaderboard("all_time", 50)
            mock_request.assert_called_once()
            mock_supabase.assert_not_called()
            self.assertIsNone(res)

    # -------------------------------------------------------------------------
    # Supabase PostgREST query parsing test
    # -------------------------------------------------------------------------
    @patch("backend.supabase_client.get_supabase_client")
    def test_get_leaderboard_from_supabase_executes_query(self, mock_get_supabase):
        """_get_leaderboard_from_supabase builds the query against leaderboard_cache."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        mock_query = MagicMock()
        mock_supabase.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query

        fake_rows = [
            {"user_id": "u-1", "display_name": "A", "total_score": 100, "rank_position": 1, "current_streak": 2, "badge_count": 1}
        ]
        mock_response = MagicMock()
        mock_response.data = fake_rows
        mock_query.execute.return_value = mock_response

        res = self.client._get_leaderboard_from_supabase("weekly", 25)
        mock_supabase.table.assert_called_once_with("leaderboard_cache")
        mock_query.select.assert_called_once_with("user_id,display_name,total_score,rank_position,current_streak,badge_count")
        mock_query.eq.assert_called_once_with("board_code", "weekly")
        mock_query.limit.assert_called_once_with(25)
        self.assertEqual(res["board_code"], "weekly")
        self.assertEqual(res["entries"], fake_rows)

    # -------------------------------------------------------------------------
    # Mock user demo fallback test
    # -------------------------------------------------------------------------
    def test_mock_user_fallback_on_unavailable(self):
        """Mock users get DEMO_LEADERBOARD when server is unavailable, without crashing."""
        with patch.object(
            leaderboard_service._repository,
            "get_leaderboard",
            side_effect=leaderboard_service.LeaderboardUnavailable("Offline"),
        ):
            entries = leaderboard_service.get_leaderboard(user_id="mock-1")
            self.assertGreater(len(entries), 0)
            self.assertTrue(any(e["user_id"] == "mock-1" for e in entries))
            self.assertTrue(any(e["is_current_user"] for e in entries))


if __name__ == "__main__":
    unittest.main()

