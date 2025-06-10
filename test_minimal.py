#!/usr/bin/env python3
"""Minimal test to verify basic functionality."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Test SecurityUtils
print("Testing SecurityUtils...")
from app.core.auth_security import SecurityUtils

# Test password hashing
password = "test_password123"
hashed = SecurityUtils.get_password_hash(password)
print(f"✓ Password hashed successfully")

# Test password verification
is_valid = SecurityUtils.verify_password(password, hashed)
print(f"✓ Password verification: {is_valid}")

# Test token creation
token_data = {"sub": "123", "email": "test@example.com"}
token = SecurityUtils.create_access_token(token_data)
print(f"✓ Access token created: {token[:20]}...")

# Test token decoding
decoded = SecurityUtils.decode_token(token)
print(f"✓ Token decoded successfully: sub={decoded.get('sub')}")

print("\nAll basic security tests passed!")