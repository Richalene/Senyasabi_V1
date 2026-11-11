import runpy
import sys
import threading
import traceback
from pathlib import Path


def run_backend():
    """Runs the backend module in the background."""
    try:
        runpy.run_module(
            "senyasabi.backend.main",
            run_name="__main__"
        )
    except Exception:
        # Log backend-specific errors if needed
        raise


def main():
    project_root = Path(__file__).resolve().parent
    senyasabi_dir = project_root / "senyasabi"
    app_path = senyasabi_dir / "main.py"

    try:
        # Ensure both the project root and senyasabi directory
        # are discoverable by Python.
        sys.path.insert(0, str(project_root))
        sys.path.insert(0, str(senyasabi_dir))

        # 1. Start the backend in a background daemon thread
        backend_thread = threading.Thread(target=run_backend, daemon=True)
        backend_thread.start()

        # 2. Immediately launch the desktop application (GUI) on the main thread
        # (PySide6/Qt requires the main application loop to run on the main thread)
        app_path = Path(__file__).resolve().parent / "senyasabi" / "main.py"

        sys.argv = [str(app_path)]

        runpy.run_path(
            str(app_path),
            run_name="__main__"
        )

    except Exception:
        log_path = Path.home() / "SenyaSabi_startup_error.log"
        log_path.write_text(traceback.format_exc(), encoding="utf-8")
        raise


if __name__ == "__main__":
    main()