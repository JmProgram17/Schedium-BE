#!/usr/bin/env python
"""
Code formatting script.
Runs all formatters and linters.
"""

import subprocess
import sys
from pathlib import Path


def run_tool(tool: str, args: list[str]) -> tuple[bool, str]:
    """Run a development tool and capture output."""
    try:
        result = subprocess.run([tool] + args, capture_output=True, text=True)
        return result.returncode == 0, result.stdout + result.stderr
    except FileNotFoundError:
        return False, f"{tool} not found. Please install dev dependencies."


def main():
    """Run all code quality tools."""
    print("=" * 60)
    print("🎨 Running Code Formatters and Linters")
    print("=" * 60)

    # Define tools and their arguments
    tools = [
        ("isort", [".", "--profile=black"], "Import sorting"),
        ("black", ["."], "Code formatting"),
        ("flake8", ["app", "tests"], "Linting"),
        ("mypy", ["app"], "Type checking"),
    ]

    all_passed = True

    for tool, args, description in tools:
        print(f"\n🔍 {description} ({tool})...")
        success, output = run_tool(tool, args)

        if success:
            print(f"✅ {tool} passed!")
        else:
            print(f"❌ {tool} failed!")
            print(output)
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All checks passed!")
        sys.exit(0)
    else:
        print("❌ Some checks failed. Please fix the issues.")
        sys.exit(1)


if __name__ == "__main__":
    main()
