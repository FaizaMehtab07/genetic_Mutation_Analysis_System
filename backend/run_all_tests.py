"""
Run the main test suites and print a compact summary.
"""

import subprocess
import sys
from pathlib import Path


def run_tests() -> int:
    """Run the main test files one by one."""

    backend_dir = Path(__file__).parent
    python_executable = str(backend_dir / "venv" / "Scripts" / "python.exe")
    test_files = [
        "tests/test_agents_unit.py",
        "tests/test_models_unit.py",
        "tests/test_utils_unit.py",
        "tests/test_integration_complete.py",
        "tests/test_performance.py",
        "tests/test_error_scenarios.py",
    ]

    results = {}
    total_passed = 0
    total_failed = 0

    print("=" * 80)
    print("RUNNING COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    for test_file in test_files:
        print(f"\n{'=' * 80}")
        print(f"Running: {test_file}")
        print("=" * 80)

        result = subprocess.run(
            [python_executable, "-m", "pytest", test_file, "-v", "--tb=short"],
            cwd=backend_dir,
        )

        results[test_file] = result.returncode
        if result.returncode == 0:
            print(f"PASSED: {test_file}")
            total_passed += 1
        else:
            print(f"FAILED: {test_file}")
            total_failed += 1

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_file, returncode in results.items():
        status = "PASSED" if returncode == 0 else "FAILED"
        print(f"{status}: {test_file}")

    print()
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())
