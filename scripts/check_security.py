#!/usr/bin/env python
"""
Security checking script.
Runs security tools and checks for vulnerabilities.
"""

import json
import subprocess
from pathlib import Path


def check_secrets():
    """Check for hardcoded secrets."""
    print("\n🔍 Checking for hardcoded secrets...")

    # Files to check
    files_to_check = ["app/config.py", ".env.example", "docker-compose.yml"]

    suspicious_patterns = ["password=", "secret=", "api_key=", "token="]

    issues = []

    for file_path in files_to_check:
        if Path(file_path).exists():
            with open(file_path, "r") as f:
                content = f.read().lower()
                for pattern in suspicious_patterns:
                    if pattern in content and "example" not in file_path:
                        issues.append(f"Potential secret in {file_path}")

    if issues:
        print("⚠️  Potential security issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ No hardcoded secrets detected")


def run_bandit():
    """Run Bandit security linter."""
    print("\n🔍 Running Bandit security scan...")

    try:
        result = subprocess.run(
            ["bandit", "-r", "app", "-f", "json", "-ll"], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("✅ No security issues found by Bandit")
        else:
            data = json.loads(result.stdout)
            if data.get("results"):
                print("⚠️  Security issues found:")
                for issue in data["results"]:
                    print(f"  - {issue['issue_text']} in {issue['filename']}")
    except FileNotFoundError:
        print("❌ Bandit not installed. Run: pip install bandit")
    except json.JSONDecodeError:
        print("❌ Error parsing Bandit output")


def check_dependencies():
    """Check for known vulnerabilities in dependencies."""
    print("\n🔍 Checking dependencies for vulnerabilities...")

    try:
        result = subprocess.run(["pip-audit"], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ No vulnerabilities found in dependencies")
        else:
            print("⚠️  Vulnerabilities found:")
            print(result.stdout)
    except FileNotFoundError:
        print("❌ pip-audit not installed. Run: pip install pip-audit")


def main():
    """Run all security checks."""
    print("=" * 60)
    print("🔒 Security Check Suite")
    print("=" * 60)

    check_secrets()
    run_bandit()
    check_dependencies()

    print("\n" + "=" * 60)
    print("Security check complete!")
    print("\n💡 Additional recommendations:")
    print("- Regularly update dependencies")
    print("- Use environment variables for all secrets")
    print("- Enable 2FA on all deployment accounts")
    print("- Regularly rotate API keys and passwords")


if __name__ == "__main__":
    main()
