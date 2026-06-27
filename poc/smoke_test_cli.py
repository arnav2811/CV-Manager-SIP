"""
Smoke-test the main command-line entry points.

This is not an F1 metric test. It only checks that the CLI scripts start,
accept an exit option, and return successfully.

Run from the repository root:
  python poc/smoke_test_cli.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_command(name: str, command: list[str], user_input: str = "") -> bool:
    print(f"Running {name}...")
    proc = subprocess.run(
        command,
        input=user_input,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
    )
    if proc.returncode == 0:
        print(f"OK {name}")
        return True

    print(f"FAIL {name}")
    print(proc.stdout)
    print(proc.stderr)
    return False


def main() -> int:
    python = sys.executable
    smoke_dir = Path(tempfile.mkdtemp(prefix="cv_manager_eval_smoke_"))
    checks = [
        ("RapidFuzz standalone CLI", [python, "poc/normalizer_rapidfuzz.py"], "3\n"),
        ("Dataset preparation", [python, "poc/prepare_f1_datasets.py", "--out-dir", str(smoke_dir)], ""),
        (
            "F1 evaluation smoke run",
            [python, "poc/evaluate_f1.py", "--dataset", "all", "--max-rows", "25", "--eval-dir", str(smoke_dir)],
            "",
        ),
    ]

    passed = 0
    for name, command, user_input in checks:
        if run_command(name, command, user_input):
            passed += 1

    print(f"{passed}/{len(checks)} smoke checks passed")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
