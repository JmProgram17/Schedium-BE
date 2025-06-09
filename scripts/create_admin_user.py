#!/usr/bin/env python
"""
Create initial admin user.
Run this script after setting up the database.
"""

import sys
from getpass import getpass
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.security import SecurityUtils
from app.database import SessionLocal
from app.models.auth import Role, User
from app.repositories.auth import RoleRepository, UserRepository


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

        # Check if admin users already exist
        user_repo = UserRepository(db)
        existing_admins = (
            db.query(User).join(Role).filter(Role.name == "Administrator").all()
        )

        if existing_admins:
            print("\n⚠️  Existing administrators:")
            for admin in existing_admins:
                print(f"   - {admin.first_name} {admin.last_name} ({admin.email})")

            response = input("\nCreate another admin? (y/N): ").lower()
            if response != "y":
                return True

        # Get user details
        print("\nEnter admin user details:")
        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()
        email = input("Email: ").strip()
        document_number = input("Document number: ").strip()

        # Validate inputs
        if not all([first_name, last_name, email, document_number]):
            print("❌ All fields are required!")
            return False

        # Check if email already exists
        if user_repo.get_by_email(email):
            print(f"❌ Email {email} is already registered!")
            return False

        # Check if document already exists
        if user_repo.get_by_document(document_number):
            print(f"❌ Document {document_number} is already registered!")
            return False

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

        # Create user directly with repository
        user_dict = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "document_number": document_number,
            "password": SecurityUtils.get_password_hash(password),
            "role_id": admin_role.role_id,
            "active": True,
        }

        # Create the user
        new_user = User(**user_dict)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print(f"\n✅ Admin user created successfully!")
        print(f"   ID: {new_user.user_id}")
        print(f"   Email: {new_user.email}")
        print(f"   Name: {new_user.first_name} {new_user.last_name}")
        print(f"   Role: Administrator")

        return True

    except Exception as e:
        print(f"\n❌ Error creating admin user: {e}")
        db.rollback()
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = create_admin_user()
    sys.exit(0 if success else 1)
