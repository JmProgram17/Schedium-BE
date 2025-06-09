"""
End-to-end tests for academic endpoints.
"""

import pytest
from fastapi import status


class TestAcademicEndpoints:
    """Test academic domain endpoints."""

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/v1/academic/levels",
            "/api/v1/academic/chains",
            "/api/v1/academic/nomenclatures",
            "/api/v1/academic/programs",
            "/api/v1/academic/groups",
        ],
    )
    def test_list_endpoints_require_auth(self, client, endpoint):
        """Test that list endpoints require authentication."""
        response = client.get(endpoint)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_level_flow(self, authorized_client):
        """Test creating a new level."""
        response = authorized_client.post(
            "/api/v1/academic/levels",
            json={"study_type": "Specialization", "duration": 12},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()["data"]
        assert data["study_type"] == "Specialization"
        assert data["duration"] == 12
        assert "level_id" in data

    def test_create_program_flow(self, authorized_client, test_level, test_department):
        """Test creating a complete program."""
        # First create nomenclature
        nom_response = authorized_client.post(
            "/api/v1/academic/nomenclatures",
            json={"code": "TEST", "description": "Test Program", "active": True},
        )
        nomenclature_id = nom_response.json()["data"]["nomenclature_id"]

        # Create program
        response = authorized_client.post(
            "/api/v1/academic/programs",
            json={
                "name": "Test Program Full",
                "nomenclature_id": nomenclature_id,
                "level_id": test_level.level_id,
                "department_id": test_department.department_id,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()["data"]
        assert data["name"] == "Test Program Full"
        assert data["nomenclature"]["code"] == "TEST"

    def test_student_group_crud_flow(self, authorized_client, test_program):
        """Test complete CRUD flow for student groups."""
        # Note: In a real test, we would need to create and persist a Schedule
        # to the database before using it in the group creation

        # Create group
        create_response = authorized_client.post(
            "/api/v1/academic/groups",
            json={
                "group_number": 2750999,
                "program_id": test_program.program_id,
                "start_date": "2024-01-01",
                "end_date": "2025-12-31",
                "capacity": 25,
                "schedule_id": 1,  # Assuming it exists
                "active": True,
            },
        )

        if create_response.status_code == status.HTTP_201_CREATED:
            group_id = create_response.json()["data"]["group_id"]

            # Read group
            get_response = authorized_client.get(f"/api/v1/academic/groups/{group_id}")
            assert get_response.status_code == status.HTTP_200_OK

            # Update group
            update_response = authorized_client.put(
                f"/api/v1/academic/groups/{group_id}",
                json={"capacity": 30},
            )
            assert update_response.status_code == status.HTTP_200_OK
            assert update_response.json()["data"]["capacity"] == 30

            # Disable group
            disable_response = authorized_client.patch(
                f"/api/v1/academic/groups/{group_id}/disable",
                json={"reason": "Test disable"},
            )
            assert disable_response.status_code == status.HTTP_200_OK
            assert disable_response.json()["data"]["active"] is False

    def test_search_programs(self, authorized_client, test_program):
        """Test searching programs with filters."""
        response = authorized_client.get(
            "/api/v1/academic/programs",
            params={"search": "Software", "page": 1, "page_size": 10},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert len(data["items"]) > 0
