"""
Runtime path resolution for SenyaSabi.

Provides seamless path resolution for both development mode (running from source)
and frozen PyInstaller execution (running inside extracted _MEIPASS or one-folder bundle).
"""
import sys
from pathlib import Path

def get_base_dir() -> Path:
    """Return the base directory for application resources and source code.
    
    In PyInstaller frozen mode (onefile / onedir), sys._MEIPASS holds the extracted/bundled root.
    If 'senyasabi' subfolder exists inside _MEIPASS, use it; otherwise use _MEIPASS directly.
    In raw development mode, returns the parent directory of backend (i.e. <repo>/senyasabi).
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        meipass = Path(sys._MEIPASS)
        if (meipass / "resources").exists():
            return meipass
        if (meipass / "senyasabi" / "resources").exists():
            return meipass / "senyasabi"
        return meipass
    # Development: backend is inside senyasabi/backend
    return Path(__file__).resolve().parent.parent

def get_resource_path(relative_path: str | Path) -> Path:
    """Resolve a relative resource path against the runtime base directory."""
    return get_base_dir() / relative_path

