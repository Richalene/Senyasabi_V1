"""
API client for SenyaSabi desktop application.

This client handles communication with the backend:
- In fastapi mode: HTTP requests to FastAPI backend
- In distributed mode: Direct Supabase client queries
- Token management
- Retry logic with exponential backoff
- Online/offline detection
- Request queuing when offline
"""
import logging
import time
import requests
import threading
from typing import Optional, Dict, Any, List, Callable, Tuple
from dataclasses import dataclass

from .config import FASTAPI_HOST, FASTAPI_PORT, CLIENT_MODE, API_BASE_URL, SUPABASE_ANON_KEY, PRODUCTION

log = logging.getLogger(__name__)


def _current_client_mode() -> str:
    """Get active client mode from env or config."""
    import os
    env_mode = os.getenv("SYSTEM_MODE") or os.getenv("SENYASABI_CLIENT_MODE")
    if env_mode:
        return env_mode.lower()
    from . import config
    return getattr(config, "CLIENT_MODE", CLIENT_MODE).lower()

OFFLINE_TIMEOUT = 4            # one quick probe while offline
OFFLINE_PROBE_INTERVAL = 15    # seconds between probes while offline

def _distributed_supabase_available() -> bool:
    """True when distributed mode can fall back to Supabase-direct calls."""
    if _current_client_mode() != "distributed":
        return False
    try:
        from .supabase_client import is_supabase_available
        return is_supabase_available()
    except Exception:
        return False

@dataclass
class APIConfig:
    """API client configuration."""
    base_url: str
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


class APIClient:
    """
    HTTP client for SenyaSabi API.
    
    Handles authentication, retries, and offline queuing.
    """
    
    def __init__(self, config: Optional[APIConfig] = None):
        """Initialize API client."""
        if config is None:
            config = APIConfig(base_url=API_BASE_URL.rstrip("/"))
        if PRODUCTION and not config.base_url.startswith("https://"):
            raise RuntimeError("HTTPS is required for API in production mode.")

        self.config = config
        self.access_token: Optional[str] = None
        self.offline_queue: List[Dict] = []   # compat only; the durable queue is SQLite sync_queue
        self._last_offline_probe = float("-inf")

    @property
    def is_online(self) -> bool:
        return _current_online_status

    @is_online.setter
    def is_online(self, value: bool) -> None:
        _set_online(bool(value))

    def set_access_token(self, token: str):
        """Set the Supabase access token for authentication."""
        self.access_token = token
    
    def clear_access_token(self):
        """Clear the access token."""
        self.access_token = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests.
        
        For distributed builds using anon key:
        - JWT token in Authorization header for authenticated endpoints
        - Anon key in apikey header for public endpoints
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add anon key for all requests (public endpoints need it)
        if SUPABASE_ANON_KEY:
            headers["apikey"] = SUPABASE_ANON_KEY
        
        # Add JWT token for authenticated requests
        from . import auth_service  # lazy: auth_service never imports api_client
        token = auth_service.get_access_token() or self.access_token
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        return headers
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Parsed JSON, or None when offline / rejected / failing.

        Offline: at most one short probe every OFFLINE_PROBE_INTERVAL seconds, so
        callers get their SQLite fallback immediately instead of waiting on timeouts.
        """
        if not self.is_online:
            now = time.monotonic()
            if now - self._last_offline_probe < OFFLINE_PROBE_INTERVAL:
                return None
            self._last_offline_probe = now
        attempts = self.config.max_retries if self.is_online else 1
        timeout = self.config.timeout if self.is_online else OFFLINE_TIMEOUT
        url = f"{self.config.base_url}{endpoint}"

        for attempt in range(attempts):
            headers = self._get_headers()          # fresh token each attempt
            try:
                response = requests.request(method, url, headers=headers,
                                            timeout=timeout, **kwargs)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout,
                    requests.exceptions.TooManyRedirects) as error:
                log.warning("API unreachable (%s %s): %s", method, endpoint, error)
                # In distributed mode a dead FastAPI does not mean offline:
                # Supabase-direct calls (sync, snapshots, content) still work.
                if not _distributed_supabase_available():
                    _set_online(False)
                return None
            except requests.exceptions.RequestException as error:
                log.warning("API request failed (%s %s): %s", method, endpoint, error)
                return None

            _set_online(True)                       # the server answered
            if response.status_code >= 500:
                if attempt < attempts - 1:
                    time.sleep(self.config.retry_delay * (2 ** attempt))
                    continue
                log.warning("API %s %s -> %s", method, endpoint, response.status_code)
                return None
            if response.status_code >= 400:         # retrying a 4xx never helps
                log.warning("API %s %s -> %s", method, endpoint, response.status_code)
                return None
            try:
                return response.json()
            except ValueError:
                return None
        return None
        
    def check_online(self) -> bool:
        """
        Check if the API or Supabase is accessible.
        
        Returns:
            True if online, False otherwise
        """
        mode = _current_client_mode()
        ok = False
        if mode in ("direct", "supabase"):
            from .supabase_client import is_supabase_available
            ok = is_supabase_available()
        elif mode == "distributed":
            try:
                ok = requests.get(f"{self.config.base_url}/health", timeout=2).status_code == 200
            except requests.exceptions.RequestException:
                ok = False
            if not ok:
                from .supabase_client import is_supabase_available
                ok = is_supabase_available()
        else:
            try:
                ok = requests.get(f"{self.config.base_url}/health", timeout=5).status_code == 200
            except requests.exceptions.RequestException:
                ok = False
        _set_online(ok)
        return ok

    # offline fallback 
    def request_with_fallback(self, method: str, endpoint: str, local_reader: Callable[[], Any],
                              **kwargs) -> Tuple[Any, bool]:
        """Server first; SQLite (via local_reader) when offline or the call fails.
        Returns (data, from_server)."""
        data = self._request(method, endpoint, **kwargs)
        if data is not None:
            return data, True
        return local_reader(), False

    def get_progress_snapshot(self) -> Optional[Dict]:
        """Fetch user progress snapshot from server.
        
        In distributed mode: Try FastAPI first, fall back to direct Supabase
        In direct mode: Use direct Supabase
        In fastapi mode: Use FastAPI
        """
        if CLIENT_MODE == "direct":
            from .sync_supabase import fetch_progress_snapshot
            return fetch_progress_snapshot()
        elif CLIENT_MODE == "distributed":
            # Try FastAPI first, fall back to direct Supabase
            result = self._request("GET", "/api/v1/progress/me/snapshot")
            if result is not None:
                return result
            # FastAPI unavailable, try direct Supabase
            from .sync_supabase import fetch_progress_snapshot
            return fetch_progress_snapshot()
        else:  # fastapi mode
            return self._request("GET", "/api/v1/progress/me/snapshot")

    def get_dashboard(self, user_id, local_reader: Callable[[Any], Dict]) -> Tuple[Dict, bool]:
        """Online: merge the server snapshot + content delta into SQLite, then read SQLite.
        Offline: skip straight to SQLite. Returns (dashboard_data, synced_from_server)."""
        from . import progress_sync   # lazy: avoids an import cycle
        synced = False
        try:
            synced = bool(progress_sync.pull_user_progress())   # False when offline / no session
        except Exception as error:
            log.warning("Progress pull failed, using local cache: %s", error)
        return local_reader(user_id), synced
    
    # Content sync methods
    def sync_content(self, since_version: int = 0) -> Optional[Dict]:
        """
        Fetch content delta from server.
        
        In distributed mode: Try FastAPI first, fall back to direct Supabase
        In direct mode: Use direct Supabase
        In fastapi mode: Use FastAPI
        
        Args:
            since_version: Only fetch changes since this version
            
        Returns:
            Content delta or None
        """
        if CLIENT_MODE == "direct":
            from .sync_supabase import sync_content
            return sync_content(since_version)
        elif CLIENT_MODE == "distributed":
            # Try FastAPI first, fall back to direct Supabase
            result = self._request("GET", f"/api/v1/content/sync?since_version={since_version}")
            if result is not None:
                return result
            # FastAPI unavailable, try direct Supabase
            from .sync_supabase import sync_content
            return sync_content(since_version)
        else:  # fastapi mode
            return self._request("GET", f"/api/v1/content/sync?since_version={since_version}")
    
    def get_content_version(self) -> Optional[Dict]:
        """
        Get current content version.
        
        Returns:
            Content version info or None
        """
        return self._request("GET", "/api/v1/content/version")
    
    # Progress sync methods
    def upload_sync(self, user_id: str, sync_items: List[Dict]) -> Optional[Dict]:
        """
        Upload progress and attempts to server.
        
        In distributed mode: Try FastAPI first, fall back to direct Supabase
        In direct mode: Use direct Supabase
        In fastapi mode: Use FastAPI
        
        Args:
            user_id: User ID
            sync_items: List of sync items
            
        Returns:
            Sync response or None
        """
        if CLIENT_MODE == "direct":
            from .sync_supabase import upload_sync
            return upload_sync(str(user_id), sync_items)
        elif CLIENT_MODE == "distributed":
            # Try FastAPI first, fall back to direct Supabase
            payload = {
                "user_id": user_id,
                "sync_items": sync_items
            }
            result = self._request("POST", "/api/v1/sync/upload", json=payload)
            if result is not None:
                return result
            # FastAPI unavailable, try direct Supabase
            from .sync_supabase import upload_sync
            return upload_sync(str(user_id), sync_items)
        else:  # fastapi mode
            payload = {
                "user_id": user_id,
                "sync_items": sync_items
            }
            return self._request("POST", "/api/v1/sync/upload", json=payload)
    
    def get_sync_queue(self, user_id: int) -> Optional[Dict]:
        """
        Get pending sync queue items.
        
        Args:
            user_id: User ID
            
        Returns:
            Sync queue or None
        """
        return self._request("GET", f"/api/v1/sync/queue/{user_id}")
    
    # Media methods
    def get_presigned_url(self, media_id: int) -> Optional[Dict]:
        """
        Get presigned URL for media file.
        
        Args:
            media_id: Media file ID
            
        Returns:
            Presigned URL info or None
        """
        return self._request("GET", f"/api/v1/media/presign/{media_id}")
    
    def get_media_info(self, media_id: int) -> Optional[Dict]:
        """
        Get media file information.
        
        Args:
            media_id: Media file ID
            
        Returns:
            Media info or None
        """
        return self._request("GET", f"/api/v1/media/info/{media_id}")
    
    # Progress methods
    def get_user_progress(self, user_id: int) -> Optional[Dict]:
        """
        Get user progress.
        
        Args:
            user_id: User ID
            
        Returns:
            User progress or None
        """
        return self._request("GET", f"/api/v1/progress/{user_id}")
    
    def get_user_statistics(self, user_id: int, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get user statistics.
        
        Args:
            user_id: User ID
            force_refresh: Force refresh statistics
            
        Returns:
            User statistics or None
        """
        params = {"force_refresh": force_refresh} if force_refresh else None
        return self._request("GET", f"/api/v1/progress/{user_id}/statistics", params=params)
    
    def get_user_streak(self, user_id: str) -> Optional[Dict]:
        """
        Get user streak information.

        In distributed mode: Try FastAPI first, fall back to direct Supabase
        In fastapi mode: Query FastAPI backend

        Args:
            user_id: User ID (UUID string)

        Returns:
            User streak or None
        """
        mode = _current_client_mode()
        if mode == "distributed":
            result = self._request("GET", f"/api/v1/progress/{user_id}/streak")
            if result is not None:
                return result
            return self._get_streak_from_supabase(user_id)
        else:  # fastapi mode
            return self._request("GET", f"/api/v1/progress/{user_id}/streak")

    def _get_streak_from_supabase(self, user_id: str) -> Optional[Dict]:
        """Fetch streak directly from Supabase (fallback mode)."""
        from .supabase_client import get_supabase_client
        supabase = get_supabase_client()
        if supabase is None:
            return None
        try:
            response = supabase.table('streaks').select('*').eq('user_id', user_id).execute()
            if response.data:
                row = response.data[0]
                return {
                    "user_id": row.get('user_id'),
                    "current_streak": row.get('current_streak', 0),
                    "longest_streak": row.get('longest_streak', 0),
                    "last_activity_date": row.get('last_activity_date')
                }
            return None
        except Exception as e:
            logging.getLogger(__name__).warning("Failed to fetch streak from Supabase: %s", e)
            return None
    
    # Leaderboard methods
    def get_leaderboard(self, board_code: str = "all_time", limit: int = 100) -> Optional[Dict]:
        """
        Get leaderboard.
        
        In direct mode: Query Supabase leaderboard_cache
        In distributed mode: Try FastAPI first, fall back to direct Supabase
        In fastapi mode: Query FastAPI backend
        
        Args:
            board_code: Leaderboard type (all_time, weekly, monthly)
            limit: Maximum entries
            
        Returns:
            Leaderboard or None
        """
        mode = _current_client_mode()
        if mode in ("direct", "supabase"):
            return self._get_leaderboard_from_supabase(board_code, limit)
        elif mode == "distributed":
            result = self._request("GET", f"/api/v1/leaderboard?board_code={board_code}&limit={limit}")
            if result is not None:
                return result
            return self._get_leaderboard_from_supabase(board_code, limit)
        else:  # fastapi mode
            return self._request("GET", f"/api/v1/leaderboard?board_code={board_code}&limit={limit}")

    def _get_leaderboard_from_supabase(self, board_code: str = "all_time", limit: int = 100) -> Optional[Dict]:
        """Fetch cached leaderboard directly from Supabase (fallback mode)."""
        from .supabase_client import get_supabase_client
        supabase = get_supabase_client()
        if supabase is None:
            return None
        try:
            response = (
                supabase.table("leaderboard_cache")
                .select("user_id,display_name,total_score,rank_position,current_streak,badge_count")
                .eq("board_code", board_code)
                .order("rank_position", desc=False)
                .order("display_name", desc=False)
                .limit(limit)
                .execute()
            )
            if response and hasattr(response, "data") and response.data is not None:
                return {
                    "board_code": board_code,
                    "limit": limit,
                    "entries": response.data,
                    "cached": True,
                }
            return None
        except Exception as exc:
            log.warning("Supabase leaderboard query failed: %s", type(exc).__name__)
            return None

    def get_user_leaderboard_position(self, user_id: Any, board_code: str = "all_time") -> Optional[Dict]:
        """
        Get user's leaderboard position.
        
        Args:
            user_id: User ID
            board_code: Leaderboard type
            
        Returns:
            User position or None
        """
        mode = _current_client_mode()
        if mode in ("direct", "supabase"):
            return self._get_user_position_from_supabase(user_id, board_code)
        elif mode == "distributed":
            result = self._request("GET", f"/api/v1/leaderboard/user/{user_id}?board_code={board_code}")
            if result is not None:
                return result
            return self._get_user_position_from_supabase(user_id, board_code)
        else:  # fastapi mode
            return self._request("GET", f"/api/v1/leaderboard/user/{user_id}?board_code={board_code}")

    def _get_user_position_from_supabase(self, user_id: Any, board_code: str = "all_time") -> Optional[Dict]:
        """Fetch user's leaderboard position directly from Supabase (fallback mode)."""
        from .supabase_client import get_supabase_client
        supabase = get_supabase_client()
        if supabase is None:
            return None
        try:
            response = (
                supabase.table("leaderboard_cache")
                .select("user_id,display_name,total_score,rank_position,current_streak,badge_count")
                .eq("board_code", board_code)
                .eq("user_id", str(user_id))
                .limit(1)
                .execute()
            )
            if response and hasattr(response, "data") and response.data:
                return response.data[0]
            return None
        except Exception as exc:
            log.warning("Supabase user position query failed: %s", type(exc).__name__)
            return None
    
    # User methods
    def get_user_profile(self) -> Optional[Dict]:
        """
        Get current user profile.
        
        Returns:
            User profile or None
        """
        return self._request("GET", "/api/v1/user/profile")
    
    # Offline queue management
    def process_offline_queue(self) -> int:
        """
        Process queued offline requests.
        
        Returns:
            Number of requests processed successfully
        """
        if not self.offline_queue:
            return 0
        
        processed = 0
        failed_items = []
        
        for item in self.offline_queue:
            result = self._request(item["method"], item["endpoint"], **item["kwargs"])
            if result is not None:
                processed += 1
            else:
                failed_items.append(item)
        
        self.offline_queue = failed_items
        return processed
    
    def get_queue_size(self) -> int:
        """Get number of queued offline requests."""
        return len(self.offline_queue)


# Global API client instance
_api_client: Optional[APIClient] = None


def get_api_client() -> APIClient:
    """
    Get the global API client instance.
    
    Returns:
        APIClient instance
    """
    global _api_client
    if _api_client is None:
        _api_client = APIClient()
    return _api_client


def set_api_client(client: APIClient):
    """Set the global API client instance."""
    global _api_client
    _api_client = client


# Connection Status Monitoring System
_connection_status_listeners: List[Callable[[bool], None]] = []
_listeners_lock = threading.Lock()
_current_online_status: bool = True
_status_check_interval: int = 30  # seconds
_status_check_timer: Optional[threading.Timer] = None
_monitoring: bool = False


def _set_online(online: bool) -> None:
    """Single place that flips state; notifies listeners only on a change."""
    global _current_online_status
    changed = online != _current_online_status
    _current_online_status = online
    if changed:
        log.info("Connection status: %s", "online" if online else "offline")
        _notify_connection_status_change(online)

def add_connection_status_listener(callback: Callable[[bool], None]) -> None:
    """Add a callback to be notified when connection status changes.
    
    Args:
        callback: Function that takes a boolean (True=online, False=offline)
    """
    with _listeners_lock:
        _connection_status_listeners.append(callback)


def remove_connection_status_listener(callback: Callable[[bool], None]) -> None:
    """Remove a connection status listener.
    
    Args:
        callback: The callback function to remove
    """
    with _listeners_lock:
        if callback in _connection_status_listeners:
            _connection_status_listeners.remove(callback)


def _notify_connection_status_change(online: bool) -> None:
    """Notify all listeners of connection status change."""
    with _listeners_lock:
        listeners = list(_connection_status_listeners)
    for callback in listeners:
        try:
            callback(online)
        except Exception:
            pass  # Don't let one listener failure break others


def _check_connection_status() -> None:
    global _status_check_timer
    try:
        get_api_client().check_online()      # updates state + notifies on change
    except Exception:
        _set_online(False)
    if _monitoring:
        _status_check_timer = threading.Timer(_status_check_interval, _check_connection_status)
        _status_check_timer.daemon = True
        _status_check_timer.start()

def start_connection_monitoring(interval: int = 30) -> None:
    """Start background connection status monitoring.
    
    Args:
        interval: Check interval in seconds (default: 30)
    """
    global _status_check_interval, _status_check_timer, _monitoring
    _status_check_interval = interval
    if _status_check_timer is not None:
        _status_check_timer.cancel()
    _monitoring = True
    # first probe off the UI thread: startup must not wait on /health
    threading.Thread(target=_check_connection_status, daemon=True, name="conn-monitor").start()

def stop_connection_monitoring() -> None:
    """Stop background connection status monitoring."""
    global _status_check_timer
    global _monitoring
    
    if _status_check_timer is not None:
        _monitoring = False
        _status_check_timer.cancel()
        _status_check_timer = None


def is_online() -> bool:
    """Get current connection status.
    
    Returns:
        True if online, False if offline
    """
    return _current_online_status


def get_connection_status() -> Dict[str, Any]:
    """Get detailed connection status information.
    
    Returns:
        Dict with 'online' (bool), 'queue_size' (int)
    """
    client = get_api_client()
    return {
        "online": _current_online_status,
        "queue_size": client.get_queue_size(),
    }
