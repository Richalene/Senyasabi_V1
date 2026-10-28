import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TEST_MODULES = [
    "test_audio_service",
    "test_auth",
    "test_auth_loading",
    "test_auth_token_handoff",
    "test_camera_preview",
    "test_camera_setup",
    "test_dashboard",
    "test_data_loading",
    "test_leaderboard",
    "test_leaderboard_data",
    "test_loading",
    "test_minigame_scope",
    "test_navigation",
    "test_navigation_assets",
    "test_progress_sync",
    "test_resources",
    "test_schema_drift",
    "test_startup",
    "test_ui_polish",
    "test_word_recognition",
    "test_uat_flow",
]

print(f"Running {len(TEST_MODULES)} test suites...\n", flush=True)

passed = 0
failed = []

python_bin = sys.executable

for mod in TEST_MODULES:
    f = f"{mod}.py"
    cmd = [
        python_bin,
        "-m",
        "unittest",
        f"senyasabi/tests/{f}",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT};{ROOT / 'senyasabi'};{ROOT / '.venv' / 'Lib' / 'site-packages'}"
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["TF_ENABLE_ONEDNN_OPTS"] = "0"
    env["TF_CPP_MIN_LOG_LEVEL"] = "3"

    print(f"Running {f}... ", end="", flush=True)
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=60)
    is_ok = ("\nOK" in res.stdout or "\nOK" in res.stderr) and "FAILED" not in res.stdout and "FAILED" not in res.stderr
    if is_ok or res.returncode == 0:
        print("PASS", flush=True)
        passed += 1
    else:
        print("FAIL", flush=True)
        print("--- STDOUT ---", flush=True)
        print(res.stdout, flush=True)
        print("--- STDERR ---", flush=True)
        print(res.stderr, flush=True)
        failed.append(f)

print(f"\n==========================================", flush=True)
print(f"Summary: {passed}/{len(TEST_MODULES)} test suites passed.", flush=True)
if failed:
    print(f"Failed test suites: {failed}", flush=True)
    sys.exit(1)
else:
    print("ALL TEST SUITES PASSED CLEANLY!", flush=True)
print(f"==========================================", flush=True)

sys.exit(0)

