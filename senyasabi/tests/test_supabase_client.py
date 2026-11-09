"""Tests for Supabase client factory across fastapi, distributed, and supabase/direct modes."""
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

from backend import supabase_client


class TestSupabaseClientModes(unittest.TestCase):
    def setUp(self):
        supabase_client.reset_client()

    def tearDown(self):
        supabase_client.reset_client()

    # -------------------------------------------------------------------------
    # FastAPI mode tests
    # -------------------------------------------------------------------------
    def test_fastapi_mode_returns_none(self):
        """In fastapi mode, Supabase client should always be None."""
        with patch.object(supabase_client, "CLIENT_MODE", "fastapi"), \
             patch.object(supabase_client, "SUPABASE_URL", "https://example.supabase.co"), \
             patch.object(supabase_client, "SUPABASE_ANON_KEY", "anon-secret-key"):
            self.assertIsNone(supabase_client.get_supabase_client())
            self.assertFalse(supabase_client.is_supabase_available())

    # -------------------------------------------------------------------------
    # Distributed mode tests
    # -------------------------------------------------------------------------
    @patch("supabase.create_client")
    def test_distributed_mode_with_credentials_returns_client(self, mock_create):
        """In distributed mode with credentials, fallback Supabase client is initialized."""
        mock_instance = MagicMock()
        mock_create.return_value = mock_instance

        with patch.object(supabase_client, "CLIENT_MODE", "distributed"), \
             patch.object(supabase_client, "SUPABASE_URL", "https://example.supabase.co"), \
             patch.object(supabase_client, "SUPABASE_ANON_KEY", "anon-secret-key"):
            self.assertTrue(supabase_client.is_supabase_available())
            client = supabase_client.get_supabase_client()
            self.assertIsNotNone(client)
            self.assertEqual(client, mock_instance)
            self.assertEqual(client.supabase_url, "https://example.supabase.co")
            mock_create.assert_called_once_with("https://example.supabase.co", "anon-secret-key")

    def test_distributed_mode_missing_credentials_returns_none_safely(self):
        """In distributed mode without credentials, returns None without raising RuntimeError."""
        with patch.object(supabase_client, "CLIENT_MODE", "distributed"), \
             patch.object(supabase_client, "SUPABASE_URL", None), \
             patch.object(supabase_client, "SUPABASE_ANON_KEY", None), \
             self.assertLogs("backend.supabase_client", level="WARNING") as log_capture:
            self.assertFalse(supabase_client.is_supabase_available())
            client = supabase_client.get_supabase_client()
            self.assertIsNone(client)
            # Ensure warning was logged and does not contain secrets
            self.assertTrue(any("not configured" in record.getMessage() for record in log_capture.records))

    @patch("supabase.create_client", side_effect=TypeError("options proxy error"))
    def test_distributed_mode_initialization_error_handled_gracefully(self, mock_create):
        """In distributed mode, client initialization errors return None without crashing."""
        with patch.object(supabase_client, "CLIENT_MODE", "distributed"), \
             patch.object(supabase_client, "SUPABASE_URL", "https://example.supabase.co"), \
             patch.object(supabase_client, "SUPABASE_ANON_KEY", "anon-secret-key"), \
             self.assertLogs("backend.supabase_client", level="WARNING") as log_capture:
            client = supabase_client.get_supabase_client()
            self.assertIsNone(client)
            self.assertTrue(any("TypeError" in record.getMessage() for record in log_capture.records))

    # -------------------------------------------------------------------------
    # Direct / Supabase mode tests
    # -------------------------------------------------------------------------
    @patch("supabase.create_client")
    def test_direct_mode_with_credentials_returns_client(self, mock_create):
        """In direct mode with credentials, returns Supabase client."""
        mock_instance = MagicMock()
        mock_create.return_value = mock_instance

        with patch.object(supabase_client, "CLIENT_MODE", "direct"), \
             patch.object(supabase_client, "SUPABASE_URL", "https://example.supabase.co"), \
             patch.object(supabase_client, "SUPABASE_ANON_KEY", "anon-secret-key"):
            self.assertTrue(supabase_client.is_supabase_available())
            client = supabase_client.get_supabase_client()
            self.assertIsNotNone(client)
            self.assertEqual(client, mock_instance)

    @patch("supabase.create_client")
    def test_supabase_alias_mode_with_credentials_returns_client(self, mock_create):
        """In supabase mode (alias for direct), returns Supabase client."""
        mock_instance = MagicMock()
        mock_create.return_value = mock_instance

        with patch.object(supabase_client, "CLIENT_MODE", "supabase"), \
             patch.object(supabase_client, "SUPABASE_URL", "https://example.supabase.co"), \
             patch.object(supabase_client, "SUPABASE_ANON_KEY", "anon-secret-key"):
            self.assertTrue(supabase_client.is_supabase_available())
            client = supabase_client.get_supabase_client()
            self.assertIsNotNone(client)
            self.assertEqual(client, mock_instance)

    def test_direct_mode_missing_credentials_raises_runtime_error(self):
        """In direct mode without credentials, raises RuntimeError without leaking secrets."""
        with patch.object(supabase_client, "CLIENT_MODE", "direct"), \
             patch.object(supabase_client, "SUPABASE_URL", None), \
             patch.object(supabase_client, "SUPABASE_ANON_KEY", None):
            self.assertFalse(supabase_client.is_supabase_available())
            with self.assertRaises(RuntimeError) as ctx:
                supabase_client.get_supabase_client()
            self.assertIn("must be configured", str(ctx.exception))

    def test_unknown_mode_returns_none(self):
        """Unknown mode should return None and log a warning."""
        with patch.object(supabase_client, "CLIENT_MODE", "unknown_mode"), \
             patch.object(supabase_client, "SUPABASE_URL", "https://example.supabase.co"), \
             patch.object(supabase_client, "SUPABASE_ANON_KEY", "anon-secret-key"), \
             self.assertLogs("backend.supabase_client", level="WARNING") as log_capture:
            self.assertFalse(supabase_client.is_supabase_available())
            self.assertIsNone(supabase_client.get_supabase_client())
            self.assertTrue(any("Unknown CLIENT_MODE" in record.getMessage() for record in log_capture.records))

    # -------------------------------------------------------------------------
    # Reset client test
    # -------------------------------------------------------------------------
    @patch("supabase.create_client")
    def test_reset_client(self, mock_create):
        """reset_client() resets the cached client instance."""
        mock_create.return_value = MagicMock()

        with patch.object(supabase_client, "CLIENT_MODE", "distributed"), \
             patch.object(supabase_client, "SUPABASE_URL", "https://example.supabase.co"), \
             patch.object(supabase_client, "SUPABASE_ANON_KEY", "anon-secret-key"):
            c1 = supabase_client.get_supabase_client()
            self.assertIsNotNone(c1)
            # Re-fetch returns the same cached instance
            c2 = supabase_client.get_supabase_client()
            self.assertIs(c1, c2)
            self.assertEqual(mock_create.call_count, 1)

            # Reset clears it
            supabase_client.reset_client()
            c3 = supabase_client.get_supabase_client()
            self.assertIsNotNone(c3)
            self.assertEqual(mock_create.call_count, 2)


if __name__ == "__main__":
    unittest.main()

