"""Run every evaluation suite and report pass rates per category and per test-case ID.

  python senyasabi/tests/run_pass_rate_report.py                 # everything
  python senyasabi/tests/run_pass_rate_report.py --only SEC PT   # selected categories
  SENYASABI_STRESS_SECONDS=1800 python ... --only PT             # full 30-minute stress run

Pass rate = passed / (passed + failed + errors). Skipped tests are reported separately.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import unittest
from collections import OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP_ROOT = HERE.parent
REPO_ROOT = APP_ROOT.parent
RESULTS = HERE / "results"
MARK = "@@RESULT@@"

CATEGORIES = OrderedDict([
    ("TC-F", ("Functional (Sec. 8)", ["test_functional"])),
    ("IV", ("Input validation (Sec. 9)", ["test_input_validation"])),
    ("DB", ("Database (Sec. 10)", ["test_database_ops"])),
    ("API", ("API / external services (Sec. 11)", ["test_external_services"])),
    ("PT", ("Performance (Sec. 12)", ["test_performance"])),
    ("SEC", ("Security (Sec. 13)", ["test_security"])),
    ("COMPAT", ("Compatibility (Sec. 14)", ["test_compatibility"])),
    ("UI", ("Usability / UI (Sec. 15)", ["test_usability_ui"])),
])
REGRESSION = OrderedDict([
    ("REG-001 Login", ["test_auth", "test_auth_loading", "test_auth_token_handoff"]),
    ("REG-002 Registration", ["test_auth", "test_offline_user_sync"]),
    ("REG-003 Database operations", ["test_schema_drift", "tests_backend_smoke", "test_progress_sync",
                                     "test_leaderboard_data"]),
    ("REG-004 Sign recognition & feedback", ["test_word_recognition", "test_camera_preview",
                                             "test_camera_setup"]),
    ("REG-005 Minigames", ["test_minigame_scope", "test_ui_polish"]),
    ("REG-006 Progress tracking", ["test_dashboard", "test_dashboard_wiring", "test_data_loading"]),
])
ID_RX = re.compile(r"test_(tc_f|iv|db|api|pt|sec|ui)_(\d{3})")


# ---------------------------------------------------------------- worker (one module per process)
class _Collector(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.records = []

    def _add(self, test, status, detail=""):
        lines = [l for l in str(detail).strip().splitlines() if l.strip()]
        self.records.append({"test": test.id(), "status": status, "detail": lines[-1][:300] if lines else ""})

    def addSuccess(self, test):
        super().addSuccess(test); self._add(test, "pass")

    def addFailure(self, test, err):
        super().addFailure(test, err); self._add(test, "fail", self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err); self._add(test, "error", self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason); self._add(test, "skip", reason)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            kind = "fail" if issubclass(err[0], test.failureException) else "error"
            self._add(subtest, kind, self._exc_info_to_string(err, test))


def worker(module):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
    for p in (str(HERE), str(APP_ROOT), str(REPO_ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)
    result = _Collector()
    unittest.defaultTestLoader.loadTestsFromName(module).run(result)
    sys.stdout.write("\n" + MARK + json.dumps(result.records) + "\n")
    sys.stdout.flush()
    os._exit(0)                       # do not wait for Qt / TensorFlow / camera threads


# ---------------------------------------------------------------- parent
_cache = {}


def run_module(module, timeout):
    if module in _cache:
        return _cache[module]
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", TF_CPP_MIN_LOG_LEVEL="3", TF_ENABLE_ONEDNN_OPTS="0")
    started = time.time()
    try:
        run = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", module],
                             cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=timeout)
        line = next((l for l in run.stdout.splitlines() if l.startswith(MARK)), None)
        records = json.loads(line[len(MARK):]) if line else [
            {"test": f"{module}.<crashed>", "status": "error",
             "detail": (run.stderr.strip().splitlines() or ["no output"])[-1][:300]}]
    except subprocess.TimeoutExpired:
        records = [{"test": f"{module}.<timeout>", "status": "error", "detail": f"exceeded {timeout}s"}]
    _cache[module] = (records, time.time() - started)
    return _cache[module]


def tally(records):
    c = {"pass": 0, "fail": 0, "error": 0, "skip": 0}
    for r in records:
        c[r["status"]] += 1
    executed = c["pass"] + c["fail"] + c["error"]
    c["total"], c["executed"] = len(records), executed
    c["rate"] = round(100.0 * c["pass"] / executed, 1) if executed else None
    return c


def case_id(test_id):
    m = ID_RX.search(test_id)
    return f"{m.group(1).upper().replace('_', '-')}-{m.group(2)}" if m else None


def per_id(records):
    groups = {}
    for r in records:
        cid = case_id(r["test"])
        if cid:
            groups.setdefault(cid, []).append(r["status"])
    out = {}
    for cid, statuses in sorted(groups.items()):
        bad = [s for s in statuses if s in ("fail", "error")]
        out[cid] = "FAIL" if bad else ("SKIP" if all(s == "skip" for s in statuses) else "PASS")
    return out


def fmt(rate):
    return "n/a" if rate is None else f"{rate}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker")
    ap.add_argument("--only", nargs="*", help="TC-F IV DB API PT SEC COMPAT UI REG")
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()
    if args.worker:
        worker(args.worker)

    wanted = {w.upper() for w in args.only} if args.only else None
    report, rows, failures, id_rows = {}, [], [], []

    for key, (title, modules) in CATEGORIES.items():
        if wanted and key not in wanted:
            continue
        records = []
        for module in modules:
            print(f"running {module} ...", flush=True)
            records += run_module(module, args.timeout)[0]
        t = tally(records)
        report[title] = {"summary": t, "case_ids": per_id(records), "tests": records}
        rows.append((title, t))
        id_rows += [(title, cid, status) for cid, status in per_id(records).items()]
        failures += [(title, r) for r in records if r["status"] in ("fail", "error")]

    if not wanted or "REG" in wanted:
        for title, modules in REGRESSION.items():
            records = []
            for module in modules:
                print(f"running {module} ...", flush=True)
                records += run_module(module, args.timeout)[0]
            t = tally(records)
            report[title] = {"summary": t, "modules": modules, "tests": records}
            rows.append((title, t))
            failures += [(title, r) for r in records if r["status"] in ("fail", "error")]

    all_exec = sum(t["executed"] for _, t in rows if not _.startswith("REG"))
    all_pass = sum(t["pass"] for title, t in rows if not title.startswith("REG"))

    lines = ["# SenyaSabi evaluation - pass rates", "",
             f"Generated {time.strftime('%Y-%m-%d %H:%M:%S')}", "",
             "| Category | Total | Pass | Fail | Error | Skipped | Pass rate |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for title, t in rows:
        lines.append(f"| {title} | {t['total']} | {t['pass']} | {t['fail']} | {t['error']} | "
                     f"{t['skip']} | **{fmt(t['rate'])}** |")
    if all_exec:
        lines += ["", f"**Overall (new suites, excluding regression): {all_pass}/{all_exec} = "
                      f"{round(100 * all_pass / all_exec, 1)}%**"]
    if id_rows:
        lines += ["", "## Per test-case ID", "", "| Category | ID | Result |", "|---|---|---|"]
        lines += [f"| {c} | {i} | {s} |" for c, i, s in id_rows]
    if failures:
        lines += ["", "## Failures and errors", ""]
        lines += [f"- **{c}** `{r['test']}` - {r['detail']}" for c, r in failures]

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "pass_rate_report.md").write_text("\n".join(lines), encoding="utf-8")
    (RESULTS / "pass_rate_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\n" + "\n".join(lines[:4 + len(rows) + 3]))
    print(f"\nFull report: {RESULTS / 'pass_rate_report.md'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()