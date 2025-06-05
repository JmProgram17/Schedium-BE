#!/usr/bin/env python
"""
Test basic service functionality.
Verifies that services can be instantiated and basic operations work.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_services():
    """Test that all services can be instantiated."""
    from app.database import get_db
    from app.services import (
        AuthService, AcademicService, HRService,
        InfrastructureService, SchedulingService
    )
    
    print("🔍 Testing Services...")
    
    # Get a database session
    db = next(get_db())
    
    try:
        # Test instantiation
        services = {
            "AuthService": AuthService(db),
            "AcademicService": AcademicService(db),
            "HRService": HRService(db),
            "InfrastructureService": InfrastructureService(db),
            "SchedulingService": SchedulingService(db)
        }
        
        print("✅ All services instantiated successfully!")
        
        # Test basic queries
        print("\n📋 Testing basic queries...")
        
        # Test getting roles
        roles = services["AuthService"].get_roles()
        print(f"✅ Found {len(roles)} roles")
        
        # Test getting departments
        from app.core.pagination import PaginationParams
        params = PaginationParams(page=1, page_size=10)
        
        departments = services["HRService"].get_departments(params)
        print(f"✅ Found {departments.total} departments")
        
        # Test getting days
        days = services["SchedulingService"].get_days()
        print(f"✅ Found {len(days)} days of the week")
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_services()