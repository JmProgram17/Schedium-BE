"""
End-to-end tests for HR endpoints.
"""

import pytest
from fastapi import status


class TestHREndpoints:
    """Test HR domain endpoints."""

    def test_department_crud_flow(self, authorized_client):
        """Test complete CRUD flow for departments."""
        # Create
        create_response = authorized_client.post(
            "/api/v1/hr/departments",
            json={
                "name": "Test Department",
                "email": "test.dept@example.com",
                "phone_number": "+1234567890",
            },
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        dept_id = create_response.json()["data"]["department_id"]

        # Read
        get_response = authorized_client.get(f"/api/v1/hr/departments/{dept_id}")
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["data"]["name"] == "Test Department"

        # Update
        update_response = authorized_client.put(
            f"/api/v1/hr/departments/{dept_id}", json={"name": "Updated Department"}
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["data"]["name"] == "Updated Department"

        # Delete
        delete_response = authorized_client.delete(f"/api/v1/hr/departments/{dept_id}")
        assert delete_response.status_code == status.HTTP_200_OK

        # Verify deleted
        get_deleted = authorized_client.get(f"/api/v1/hr/departments/{dept_id}")
        assert get_deleted.status_code == status.HTTP_404_NOT_FOUND

    def test_instructor_workload_flow(self, authorized_client, test_department):
        """Test instructor creation and workload tracking."""
        # Create contract with hour limit
        contract_response = authorized_client.post(
            "/api/v1/hr/contracts",
            json={"contract_type": "Part Time", "hour_limit": 20},
        )
        contract_id = contract_response.json()["data"]["contract_id"]

        # Create instructor
        instructor_response = authorized_client.post(
            "/api/v1/hr/instructors",
            json={
                "first_name": "Test",
                "last_name": "Instructor",
                "email": "test.instructor@example.com",
                "phone_number": "+1234567890",
                "contract_id": contract_id,
                "department_id": test_department.department_id,
                "active": True,
            },
        )
        assert instructor_response.status_code == status.HTTP_201_CREATED
        instructor_id = instructor_response.json()["data"]["instructor_id"]

        # Check workload
        workload_response = authorized_client.get(
            f"/api/v1/hr/instructors/{instructor_id}/workload"
        )
        assert workload_response.status_code == status.HTTP_200_OK

        workload = workload_response.json()["data"]
        assert workload["total_hours"] == 0
        assert workload["contract_limit"] == 20
        assert workload["available_hours"] == 20
        assert workload["utilization_percentage"] == 0
        assert workload["status"] == "LOW_LOAD"

    def test_instructor_search_filters(self, authorized_client, test_department):
        """Test instructor search with various filters."""
        # Create multiple instructors
        for i in range(3):
            authorized_client.post(
                "/api/v1/hr/instructors",
                json={
                    "first_name": f"Instructor{i}",
                    "last_name": "Test",
                    "email": f"instructor{i}@example.com",
                    "department_id": test_department.department_id,
                    "active": i % 2 == 0,  # Alternate active status
                },
            )

        # Search by department
        dept_response = authorized_client.get(
            "/api/v1/hr/instructors",
            params={"department_id": test_department.department_id},
        )
        assert dept_response.status_code == status.HTTP_200_OK
        assert len(dept_response.json()["data"]["items"]) >= 3

        # Search active only
        active_response = authorized_client.get(
            "/api/v1/hr/instructors", params={"active": True}
        )
        assert active_response.status_code == status.HTTP_200_OK
        assert all(inst["active"] for inst in active_response.json()["data"]["items"])

        # Search by name
        search_response = authorized_client.get(
            "/api/v1/hr/instructors", params={"search": "Instructor1"}
        )
        assert search_response.status_code == status.HTTP_200_OK
        items = search_response.json()["data"]["items"]
        assert any("Instructor1" in inst["first_name"] for inst in items)

    def test_contract_deletion_protection(self, authorized_client):
        """Test that contracts with instructors cannot be deleted."""
        # Create contract
        contract_response = authorized_client.post(
            "/api/v1/hr/contracts",
            json={"contract_type": "Protected Contract", "hour_limit": 40},
        )
        contract_id = contract_response.json()["data"]["contract_id"]

        # Create instructor with this contract
        authorized_client.post(
            "/api/v1/hr/instructors",
            json={
                "first_name": "Protected",
                "last_name": "Instructor",
                "email": "protected@example.com",
                "contract_id": contract_id,
            },
        )

        # Try to delete contract
        delete_response = authorized_client.delete(
            f"/api/v1/hr/contracts/{contract_id}"
        )
        assert delete_response.status_code == status.HTTP_400_BAD_REQUEST
        assert "in use" in delete_response.json()["detail"].lower()
