#!/usr/bin/env python
"""
Generate a secure secret key for the application.
"""
import sys
import secrets
import string

from pathlib import Path

project_root = Path(__file__).parent
if (project_root / "app").exists():
    sys.path.insert(0, str(project_root))
elif (project_root.parent / "app").exists():
    sys.path.insert(0, str(project_root.parent))

def generate_secret_key(length=32):
    """Generate a cryptographically secure secret key."""
    # Use URL-safe characters
    alphabet = string.ascii_letters + string.digits + "-_"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def main():
    print("=" * 60)
    print("Secret Key Generator")
    print("=" * 60)
    
    # Generate different options
    print("\n🔐 Generated Secret Keys (choose one):\n")
    
    # Option 1: URL-safe base64
    key1 = secrets.token_urlsafe(32)
    print(f"Option 1 (URL-safe):\n{key1}\n")
    
    # Option 2: Hex
    key2 = secrets.token_hex(32)
    print(f"Option 2 (Hex):\n{key2}\n")
    
    # Option 3: Custom alphanumeric
    key3 = generate_secret_key(64)
    print(f"Option 3 (Alphanumeric):\n{key3}\n")
    
    print("📋 Instructions:")
    print("1. Copy one of the keys above")
    print("2. Replace the SECRET_KEY value in your .env file")
    print("3. Make sure to keep this key secret and secure!")
    print("\n⚠️  WARNING: Never commit the real secret key to version control!")


if __name__ == "__main__":
    main()