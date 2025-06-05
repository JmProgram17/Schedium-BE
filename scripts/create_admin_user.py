#!/usr/bin/env python
"""
Create initial admin user.
Run this script after setting up the database.
"""

import sys
from pathlib import Path
from getpass import getpass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import SessionLocal
from app.services.auth import AuthService
from app.schemas.auth import UserCreate
from app.repositories.auth import RoleRepository


def create_admin_user():
    """Create initial admin user."""
    print("=" * 60)
    print("Create Admin User")
    print("=" * 60)
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Check if admin role exists
        role_repo = RoleRepository(db)
        admin_role = role_repo.get_by_name("Administrator")
        
        if not admin_role:
            print("❌ Administrator role not found!")
            print("Make sure database migrations have been run.")
            return False
        
        # Get user details
        print("\nEnter admin user details:")
        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()
        email = input("Email: ").strip()
        document_number = input("Document number: ").strip()
        
        # Get password securely
        while True:
            password = getpass("Password (min 8 chars): ")
            if len(password) < 8:
                print("❌ Password must be at least 8 characters!")
                continue
            
            confirm_password = getpass("Confirm password: ")
            if password != confirm_password:
                print("❌ Passwords don't match!")
                continue
            
            break
        
        # Create user
        service = AuthService(db)
        
        user_data = UserCreate(
            first_name=first_name,
            last_name=last_name,
            email=email,
            document_number=document_number,
            password=password,
            role_id=admin_role.role_id,
            active=True
        )
        
        user = service.create_user(user_data)
        
        print(f"\n✅ Admin user created successfully!")
        print(f"   ID: {user.user_id}")
        print(f"   Email: {user.email}")
        print(f"   Role: {admin_role.name}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating admin user: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = create_admin_user()
    sys.exit(0 if success else 1)