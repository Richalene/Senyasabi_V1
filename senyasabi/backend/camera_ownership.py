"""A process-local lease prevents overlapping camera initialization during navigation."""
from threading import Lock

_lock = Lock()
_owner = None


def claim(owner):
    global _owner
    with _lock:
        if _owner is not None and _owner is not owner:
            return False
        _owner = owner
        return True


def release(owner):
    global _owner
    with _lock:
        if _owner is owner:
            _owner = None
