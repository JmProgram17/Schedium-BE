#!/usr/bin/env python
"""
Create default roles including a basic User role.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import SessionLocal
from app.repositories.auth import RoleRepository
from app.schemas.auth import RoleCreate


def create_default_roles():
    """Create default roles if they don't exist."""
    print("=" * 60)
    print("Creating Default Roles")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        role_repo = RoleRepository(db)
        
        # Define default roles
        default_roles = [
            "Administrator",
            "Coordinator", 
            "Secretary",
            "User"  # New basic user role
        ]
        
        created_count = 0
        
        for role_name in default_roles:
            existing = role_repo.get_by_name(role_name)
            if not existing:
                role = role_repo.create(obj_in=RoleCreate(name=role_name))
                print(f"✅ Created role: {role_name}")
                created_count += 1
            else:
                print(f"ℹ️  Role already exists: {role_name}")
        
        print(f"\n✅ Process completed. Created {created_count} new roles.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = create_default_roles()
    sys.exit(0 if success else 1)