#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: runner.py - Smoke Test Runner Handler
# Date: 2026-02-15
# Version: 1.0.0
# Category: test/handlers/testing
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-15): Initial implementation - subprocess pytest runner
#
# CODE STANDARDS:
#   - Handlers return data, never print (module handles display)
#   - No Prax logger imports (Seed standard for handlers)
#   - Google-style docstrings, type hints on all functions
# =============================================

"""Smoke test runner handler.

Invokes pytest via subprocess to run smoke tests with optional branch
filtering. Returns structured results for the module to display.
"""

import re
import subprocess
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PYTHON_BIN: str = "/home/aipass/.venv/bin/python3"
TEST_DIR: Path = Path("/home/aipass/aipass_os/dev_central/test")
SMOKE_DIR: str = "tests/smoke/"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_smoke_tests(
    branch: Optional[str] = None,
    verbose: bool = False,
) -> dict:
    """Run smoke tests via subprocess and return structured results.

    Invokes pytest programmatically using subprocess for clean isolation.
    Optionally filters tests to a specific branch using pytest's -k flag.

    Args:
        branch: Branch name to filter tests (e.g., "DRONE"). Uses pytest
            -k flag for keyword filtering. None runs all smoke tests.
        verbose: If True, passes -v flag to pytest for verbose output.

    Returns:
        Dict with keys:
            success (bool): True if all tests passed.
            total (int): Total number of tests collected.
            passed (int): Number of tests that passed.
            failed (int): Number of tests that failed.
            skipped (int): Number of tests that were skipped.
            errors (int): Number of tests with errors.
            output (str): Full pytest stdout/stderr output.
            return_code (int): pytest process return code.
    """
    cmd = [
        PYTHON_BIN, "-m", "pytest",
        SMOKE_DIR,
        "-m", "smoke",
    ]

    if verbose:
        cmd.append("-v")

    if branch:
        cmd.extend(["-k", branch])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(TEST_DIR),
        timeout=120,
    )

    output = result.stdout + result.stderr
    counts = _parse_summary(output)

    return {
        "success": result.returncode == 0,
        "total": counts["total"],
        "passed": counts["passed"],
        "failed": counts["failed"],
        "skipped": counts["skipped"],
        "errors": counts["errors"],
        "output": output,
        "return_code": result.returncode,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_summary(output: str) -> dict:
    """Parse pytest summary line to extract test counts.

    Looks for the standard pytest summary format, e.g.:
        '= 319 passed in 12.34s ='
        '= 5 failed, 314 passed, 1 skipped in 12.34s ='

    Args:
        output: Full pytest output string.

    Returns:
        Dict with keys: total, passed, failed, skipped, errors.
    """
    passed = 0
    failed = 0
    skipped = 0
    errors = 0

    # Match pytest summary line patterns
    passed_match = re.search(r"(\d+) passed", output)
    failed_match = re.search(r"(\d+) failed", output)
    skipped_match = re.search(r"(\d+) skipped", output)
    errors_match = re.search(r"(\d+) error", output)

    if passed_match:
        passed = int(passed_match.group(1))
    if failed_match:
        failed = int(failed_match.group(1))
    if skipped_match:
        skipped = int(skipped_match.group(1))
    if errors_match:
        errors = int(errors_match.group(1))

    total = passed + failed + skipped + errors

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
    }
