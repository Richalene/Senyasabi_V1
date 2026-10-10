"""
Secure credential store for refresh tokens using OS native credential managers.

Uses the 'keyring' library to store tokens securely:
- macOS: Keychain
- Windows: Credential Manager
- Linux: Secret Service API (gnome-keyring, kwallet, etc.)
"""
import sys
from typing import Optional

try:
    import keyring
    from keyring.errors import KeyringError
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    print("Warning: keyring library not installed. Refresh tokens will not be stored securely.")
    print("Install with: pip install keyring")


class CredentialStore:
    """OS-native secure credential store for refresh tokens."""

    SERVICE_NAME = "Senyasabi"

    @classmethod
    def is_available(cls) -> bool:
        """Check if the credential store is available."""
        return KEYRING_AVAILABLE

    @classmethod
    def store_refresh_token(cls, user_id: int, refresh_token: str) -> bool:
        """
        Store a refresh token securely in the OS credential store.

        Args:
            user_id: The user's ID (used as username in keyring)
            refresh_token: The refresh token to store

        Returns:
            True if successful, False otherwise
        """
        if not cls.is_available():
            print("Warning: Credential store not available. Token not stored.")
            return False

        try:
            username = str(user_id)
            keyring.set_password(cls.SERVICE_NAME, username, refresh_token)
            return True
        except KeyringError as e:
            print(f"Error storing refresh token: {e}")
            return False

    @classmethod
    def get_refresh_token(cls, user_id: int) -> Optional[str]:
        """
        Retrieve a refresh token from the OS credential store.

        Args:
            user_id: The user's ID

        Returns:
            The refresh token if found, None otherwise
        """
        if not cls.is_available():
            return None

        try:
            username = str(user_id)
            token = keyring.get_password(cls.SERVICE_NAME, username)
            return token
        except KeyringError as e:
            print(f"Error retrieving refresh token: {e}")
            return None

    @classmethod
    def delete_refresh_token(cls, user_id: int) -> bool:
        """
        Delete a refresh token from the OS credential store.

        Args:
            user_id: The user's ID

        Returns:
            True if successful, False otherwise
        """
        if not cls.is_available():
            return False

        try:
            username = str(user_id)
            keyring.delete_password(cls.SERVICE_NAME, username)
            return True
        except KeyringError as e:
            # Token might not exist, which is fine
            if "not found" in str(e).lower():
                return True
            print(f"Error deleting refresh token: {e}")
            return False

    @classmethod
    def clear_all_tokens(cls) -> int:
        """
        Clear all refresh tokens for the application.

        Returns:
            Number of tokens cleared
        """
        if not cls.is_available():
            return 0

        try:
            # keyring doesn't provide a direct way to list all credentials
            # This is a limitation of the library
            # For now, we'll just log that this operation is not supported
            print("Warning: Clearing all tokens is not supported via keyring library.")
            print("Use OS-specific tools to clear credentials if needed.")
            return 0
        except Exception as e:
            print(f"Error clearing tokens: {e}")
            return 0


# Fallback in-memory store for development/testing when keyring is not available
class InMemoryCredentialStore:
    """Fallback in-memory credential store (NOT SECURE - for development only)."""

    _tokens: dict[int, str] = {}

    @classmethod
    def is_available(cls) -> bool:
        return True

    @classmethod
    def store_refresh_token(cls, user_id: int, refresh_token: str) -> bool:
        cls._tokens[user_id] = refresh_token
        return True

    @classmethod
    def get_refresh_token(cls, user_id: int) -> Optional[str]:
        return cls._tokens.get(user_id)

    @classmethod
    def delete_refresh_token(cls, user_id: int) -> bool:
        if user_id in cls._tokens:
            del cls._tokens[user_id]
            return True
        return False

    @classmethod
    def clear_all_tokens(cls) -> int:
        count = len(cls._tokens)
        cls._tokens.clear()
        return count


def get_credential_store() -> CredentialStore | InMemoryCredentialStore:
    """
    Get the appropriate credential store instance.

    Returns:
        CredentialStore if keyring is available, InMemoryCredentialStore otherwise
    """
    if CredentialStore.is_available():
        return CredentialStore
    else:
        print("Using in-memory credential store (NOT SECURE - for development only)")
        return InMemoryCredentialStore
