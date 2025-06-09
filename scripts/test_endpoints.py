#!/usr/bin/env python
"""
Test API endpoints availability.
Verifies that all endpoints are properly registered.
"""
import sys
from pathlib import Path
from typing import Dict, List

import requests

project_root = Path(__file__).parent
if (project_root / "app").exists():
    sys.path.insert(0, str(project_root))
elif (project_root.parent / "app").exists():
    sys.path.insert(0, str(project_root.parent))

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"


def get_openapi_spec() -> Dict:
    """Get OpenAPI specification from the API."""
    response = requests.get(f"{API_URL}/openapi.json")
    response.raise_for_status()
    return response.json()


def analyze_endpoints(spec: Dict) -> Dict[str, List[str]]:
    """Analyze endpoints from OpenAPI spec."""
    endpoints_by_tag = {}

    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if method in ["get", "post", "put", "patch", "delete"]:
                tags = details.get("tags", ["untagged"])
                for tag in tags:
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []
                    endpoints_by_tag[tag].append(f"{method.upper()} {path}")

    return endpoints_by_tag


def main():
    """Main function to test endpoints."""
    print("🔍 Checking API Endpoints...")
    print(f"Base URL: {API_URL}\n")

    try:
        # Get OpenAPI spec
        spec = get_openapi_spec()
        print(f"✅ OpenAPI spec retrieved successfully")
        print(f"API Title: {spec.get('info', {}).get('title')}")
        print(f"API Version: {spec.get('info', {}).get('version')}\n")

        # Analyze endpoints
        endpoints = analyze_endpoints(spec)

        # Display results
        total_endpoints = 0
        for tag, endpoint_list in sorted(endpoints.items()):
            print(f"📋 {tag.upper()} ({len(endpoint_list)} endpoints):")
            for endpoint in sorted(endpoint_list):
                print(f"   {endpoint}")
            print()
            total_endpoints += len(endpoint_list)

        print(f"📊 SUMMARY:")
        print(f"   Total Tags: {len(endpoints)}")
        print(f"   Total Endpoints: {total_endpoints}")

        # Expected counts
        expected = {
            "authentication": 14,
            "academic": 25,
            "human-resources": 17,
            "infrastructure": 13,
            "scheduling": 23,
            "health": 3,
        }

        print(f"\n📋 VALIDATION:")
        for tag, expected_count in expected.items():
            actual_count = len(endpoints.get(tag, []))
            status = "✅" if actual_count >= expected_count else "❌"
            print(f"   {status} {tag}: {actual_count}/{expected_count}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure the API server is running:")
        print("python -m uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
