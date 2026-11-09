import runpy
import sys
import threading
import traceback
from pathlib import Path

LOG = Path.home() / "SenyaSabi_startup_error.log"


def run_backend():
    try:
        runpy.run_module("backend.main", run_name="__main__")
    except Exception:
        LOG.with_name("SenyaSabi_backend_error.log").write_text(
            traceback.format_exc(), encoding="utf-8"
        )
        raise


def main():
    try:
        # Needed for source runs so bare imports work. Harmless when frozen.
        sys.path.insert(0, str(Path(__file__).resolve().parent / "senyasabi"))

        threading.Thread(target=run_backend, daemon=True).start()
        runpy.run_module("main", run_name="__main__")
    except Exception:
        LOG.write_text(traceback.format_exc(), encoding="utf-8")
        raise


if __name__ == "__main__":
    main()