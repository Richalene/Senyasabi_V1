import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TEST_MODULES = [
    # existing suites
    "test_audio_service", "test_auth", "test_auth_loading", "test_auth_token_handoff",
    "test_camera_preview", "test_camera_setup", "test_dashboard", "test_data_loading",
    "test_leaderboard", "test_leaderboard_data", "test_loading", "test_minigame_scope",
    "test_navigation", "test_navigation_assets", "test_progress_sync", "test_resources",
    "test_schema_drift", "test_startup", "test_ui_polish", "test_word_recognition",
    "test_uat_flow",
    # evaluation suites (testing-report sections 8-15)
    "test_functional", "test_input_validation", "test_database_ops", "test_external_services",
    "test_performance", "test_security", "test_compatibility", "test_usability_ui",
]

print(f"Running {len(TEST_MODULES)} test suites...\n", flush=True)

passed, failed = 0, []
for mod in TEST_MODULES:
    f = f"{mod}.py"
    cmd = [sys.executable, "-m", "unittest", f"senyasabi/tests/{f}"]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT), str(ROOT / "senyasabi")])
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["TF_ENABLE_ONEDNN_OPTS"] = "0"
    env["TF_CPP_MIN_LOG_LEVEL"] = "3"

    print(f"Running {f}... ", end="", flush=True)
    res = subprocess.run(cmd, env=env, cwd=ROOT, capture_output=True, text=True, timeout=300)
    if res.returncode == 0:
        print("PASS", flush=True)
        passed += 1
    else:
        print("FAIL", flush=True)
        print("--- STDERR (tail) ---\n" + res.stderr[-3000:], flush=True)
        failed.append(f)

print(f"\nSummary: {passed}/{len(TEST_MODULES)} test suites passed.", flush=True)
if failed:
    print(f"Failed test suites: {failed}", flush=True)
    sys.exit(1)
print("ALL TEST SUITES PASSED CLEANLY!", flush=True)