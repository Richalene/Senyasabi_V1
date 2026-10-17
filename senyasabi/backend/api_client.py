"""
API client for SenyaSabi desktop application.

This client handles communication with the FastAPI backend:
- HTTP requests with authentication
- Token management
- Retry logic with exponential backoff
- Online/offline detection
- Request queuing when offline
"""
import os
import time
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .config import FASTAPI_HOST, FASTAPI_PORT


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
            base_url = f"http://{FASTAPI_HOST}:{FASTAPI_PORT}"
            config = APIConfig(base_url=base_url)
        
        self.config = config
        self.access_token: Optional[str] = None
        self.is_online = True
        self.offline_queue: List[Dict] = []
    
    def set_access_token(self, token: str):
        """Set the Supabase access token for authentication."""
        self.access_token = token
    
    def clear_access_token(self):
        """Clear the access token."""
        self.access_token = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json"
        }
        from . import auth_service  # lazy: auth_service never imports api_client
        token = auth_service.get_access_token() or self.access_token
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """
        Make an HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for requests
            
        Returns:
            Response JSON or None on failure
        """
        url = f"{self.config.base_url}{endpoint}"
        headers = self._get_headers()
        
        for attempt in range(self.config.max_retries):
            try:
                response = requests.request(
                    method,
                    url,
                    headers=headers,
                    timeout=self.config.timeout,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2 ** attempt)
                    print(f"Request failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    print(f"Request failed after {self.config.max_retries} attempts: {e}")
                    # Queue request if offline
                    if not self.is_online:
                        self.offline_queue.append({
                            "method": method,
                            "endpoint": endpoint,
                            "kwargs": kwargs
                        })
                    return None
        
        return None
    
    def check_online(self) -> bool:
        """
        Check if the API is accessible.
        
        Returns:
            True if online, False otherwise
        """
        try:
            response = requests.get(
                f"{self.config.base_url}/health",
                timeout=5
            )
            self.is_online = response.status_code == 200
            return self.is_online
        except requests.exceptions.RequestException:
            self.is_online = False
            return False
    
    # Content sync methods
    def sync_content(self, since_version: int = 0) -> Optional[Dict]:
        """
        Fetch content delta from server.
        
        Args:
            since_version: Only fetch changes since this version
            
        Returns:
            Content delta or None
        """
        return self._request("GET", f"/api/v1/content/sync?since_version={since_version}")
    
    def get_content_version(self) -> Optional[Dict]:
        """
        Get current content version.
        
        Returns:
            Content version info or None
        """
        return self._request("GET", "/api/v1/content/version")
    
    # Progress sync methods
    def upload_sync(self, user_id: int, sync_items: List[Dict]) -> Optional[Dict]:
        """
        Upload progress and attempts to server.
        
        Args:
            user_id: User ID
            sync_items: List of sync items
            
        Returns:
            Sync response or None
        """
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
    
    def get_user_streak(self, user_id: int) -> Optional[Dict]:
        """
        Get user streak information.
        
        Args:
            user_id: User ID
            
        Returns:
            User streak or None
        """
        return self._request("GET", f"/api/v1/progress/{user_id}/streak")
    
    # Leaderboard methods
    def get_leaderboard(self, board_code: str = "all_time", limit: int = 100) -> Optional[Dict]:
        """
        Get leaderboard.
        
        Args:
            board_code: Leaderboard type (all_time, weekly, monthly)
            limit: Maximum entries
            
        Returns:
            Leaderboard or None
        """
        return self._request("GET", f"/api/v1/leaderboard?board_code={board_code}&limit={limit}")
    
    def get_user_leaderboard_position(self, user_id: int, board_code: str = "all_time") -> Optional[Dict]:
        """
        Get user's leaderboard position.
        
        Args:
            user_id: User ID
            board_code: Leaderboard type
            
        Returns:
            User position or None
        """
        return self._request("GET", f"/api/v1/leaderboard/user/{user_id}?board_code={board_code}")
    
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
