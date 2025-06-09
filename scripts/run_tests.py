#!/usr/bin/env python
"""
Test runner script with various options.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> int:
    """Run a command and return exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def main():
    """Run tests based on arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="Run tests for Schedium Backend")
    parser.add_argument(
        "type",
        choices=["all", "unit", "integration", "e2e", "coverage"],
        default="all",
        nargs="?",
        help="Type of tests to run",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--failfast", "-x", action="store_true", help="Stop on first failure"
    )
    parser.add_argument(
        "--parallel", "-n", action="store_true", help="Run tests in parallel"
    )
    parser.add_argument("--marker", "-m", help="Run tests with specific marker")

    args = parser.parse_args()

    # Base command
    cmd = ["pytest"]

    # Add verbosity
    if args.verbose:
        cmd.append("-vv")

    # Add fail fast
    if args.failfast:
        cmd.append("-x")

    # Add parallel
    if args.parallel:
        cmd.extend(["-n", "auto"])

    # Add marker
    if args.marker:
        cmd.extend(["-m", args.marker])

    # Add test type
    if args.type == "unit":
        cmd.extend(["tests/unit", "-m", "unit"])
    elif args.type == "integration":
        cmd.extend(["tests/integration", "-m", "integration"])
    elif args.type == "e2e":
        cmd.extend(["tests/e2e", "-m", "e2e"])
    elif args.type == "coverage":
        cmd.extend(
            [
                "--cov=app",
                "--cov-report=html",
                "--cov-report=term-missing",
                "--cov-report=xml",
            ]
        )

    # Run tests
    exit_code = run_command(cmd)

    # Open coverage report if generated
    if args.type == "coverage" and exit_code == 0:
        coverage_path = Path("htmlcov/index.html")
        if coverage_path.exists():
            print(f"\nCoverage report generated: {coverage_path}")
            print("Run 'python -m http.server 8080 -d htmlcov' to view")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
