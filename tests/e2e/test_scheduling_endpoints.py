"""
End-to-end tests for scheduling endpoints.
"""

from datetime import date, time

import pytest
from fastapi import status


class TestSchedulingEndpoints:
    """Test scheduling domain endpoints."""

    def test_schedule_crud_flow(self, authorized_client):
        """Test complete CRUD flow for schedules."""
        # Create
        create_response = authorized_client.post(
            "/api/v1/scheduling/schedules",
            json={
                "name": "Night Shift",
                "start_time": "18:00:00",
                "end_time": "22:00:00",
            },
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        schedule_id = create_response.json()["data"]["schedule_id"]

        # Read
        get_response = authorized_client.get(
            f"/api/v1/scheduling/schedules/{schedule_id}"
        )
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["data"]["name"] == "Night Shift"

        # Update
        update_response = authorized_client.put(
            f"/api/v1/scheduling/schedules/{schedule_id}",
            json={"name": "Evening Shift"},
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["data"]["name"] == "Evening Shift"

        # List all
        list_response = authorized_client.get("/api/v1/scheduling/schedules")
        assert list_response.status_code == status.HTTP_200_OK
        assert any(
            s["schedule_id"] == schedule_id
            for s in list_response.json()["data"]["items"]
        )

    def test_time_block_overlap_validation(self, authorized_client):
        """Test time block overlap validation."""
        # Create first time block
        first_response = authorized_client.post(
            "/api/v1/scheduling/time-blocks",
            json={"start_time": "08:00:00", "end_time": "10:00:00"},
        )
        assert first_response.status_code == status.HTTP_201_CREATED

        # Try to create overlapping time block
        overlap_response = authorized_client.post(
            "/api/v1/scheduling/time-blocks",
            json={
                "start_time": "09:00:00",  # Overlaps with first
                "end_time": "11:00:00",
            },
        )
        # Should succeed as time blocks can overlap
        # Only the combination with days matters
        assert overlap_response.status_code == status.HTTP_201_CREATED

    def test_quarter_management(self, authorized_client):
        """Test quarter creation and management."""
        # Create quarter
        quarter_response = authorized_client.post(
            "/api/v1/scheduling/quarters",
            json={"start_date": "2024-07-01", "end_date": "2024-09-30"},
        )
        assert quarter_response.status_code == status.HTTP_201_CREATED
        _ = quarter_response.json()["data"]["quarter_id"]

        # Get current quarter (might be None)
        current_response = authorized_client.get("/api/v1/scheduling/quarters/current")
        assert current_response.status_code == status.HTTP_200_OK

        # Try to create overlapping quarter
        overlap_response = authorized_client.post(
            "/api/v1/scheduling/quarters",
            json={"start_date": "2024-08-01", "end_date": "2024-10-31"},  # Overlaps
        )
        assert overlap_response.status_code == status.HTTP_409_CONFLICT
        assert "overlap" in overlap_response.json()["detail"].lower()

    def test_class_schedule_validation(
        self, authorized_client, test_program, test_department
    ):
        """Test class schedule creation with validation."""
        # First, create all necessary entities

        # Create instructor
        instructor_response = authorized_client.post(
            "/api/v1/hr/instructors",
            json={
                "first_name": "Schedule",
                "last_name": "Test",
                "email": "schedule.test@example.com",
                "department_id": test_department.department_id,
            },
        )
        instructor_id = instructor_response.json()["data"]["instructor_id"]

        # Create campus and classroom
        campus_response = authorized_client.post(
            "/api/v1/infrastructure/campuses",
            json={"address": "123 Schedule Test St", "email": "campus@schedule.test"},
        )
        campus_id = campus_response.json()["data"]["campus_id"]

        classroom_response = authorized_client.post(
            "/api/v1/infrastructure/classrooms",
            json={"room_number": "S101", "capacity": 30, "campus_id": campus_id},
        )
        classroom_id = classroom_response.json()["data"]["classroom_id"]

        # Create schedule and group
        schedule_response = authorized_client.post(
            "/api/v1/scheduling/schedules",
            json={
                "name": "Test Schedule",
                "start_time": "08:00:00",
                "end_time": "14:00:00",
            },
        )
        schedule_id = schedule_response.json()["data"]["schedule_id"]

        group_response = authorized_client.post(
            "/api/v1/academic/groups",
            json={
                "group_number": 2750777,
                "program_id": test_program.program_id,
                "start_date": str(date.today()),
                "end_date": str(date.today().replace(year=date.today().year + 1)),
                "capacity": 25,
                "schedule_id": schedule_id,
            },
        )
        group_id = group_response.json()["data"]["group_id"]

        # Create quarter and time components
        quarter_response = authorized_client.post(
            "/api/v1/scheduling/quarters",
            json={
                "start_date": str(date.today()),
                "end_date": str(date.today().replace(month=date.today().month + 3)),
            },
        )
        quarter_id = quarter_response.json()["data"]["quarter_id"]

        time_block_response = authorized_client.post(
            "/api/v1/scheduling/time-blocks",
            json={"start_time": "08:00:00", "end_time": "10:00:00"},
        )
        time_block_id = time_block_response.json()["data"]["time_block_id"]

        # Get Monday
        days_response = authorized_client.get("/api/v1/scheduling/days")
        monday = next(d for d in days_response.json()["data"] if d["name"] == "Monday")

        # Create day-time block
        dtb_response = authorized_client.post(
            "/api/v1/scheduling/day-time-blocks",
            json={"day_id": monday["day_id"], "time_block_id": time_block_id},
        )
        dtb_id = dtb_response.json()["data"]["day_time_block_id"]

        # First validate the schedule
        validate_response = authorized_client.post(
            "/api/v1/scheduling/class-schedules/validate",
            json={
                "subject": "Test Subject",
                "quarter_id": quarter_id,
                "day_time_block_id": dtb_id,
                "group_id": group_id,
                "instructor_id": instructor_id,
                "classroom_id": classroom_id,
            },
        )
        assert validate_response.status_code == status.HTTP_200_OK
        validation = validate_response.json()["data"]
        assert validation["is_valid"] is True
        assert len(validation["conflicts"]) == 0

        # Create the schedule
        create_response = authorized_client.post(
            "/api/v1/scheduling/class-schedules",
            json={
                "subject": "Test Subject",
                "quarter_id": quarter_id,
                "day_time_block_id": dtb_id,
                "group_id": group_id,
                "instructor_id": instructor_id,
                "classroom_id": classroom_id,
            },
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        schedule_id = create_response.json()["data"]["class_schedule_id"]

        # Try to create conflicting schedule (same instructor, same time)
        conflict_response = authorized_client.post(
            "/api/v1/scheduling/class-schedules",
            json={
                "subject": "Conflicting Subject",
                "quarter_id": quarter_id,
                "day_time_block_id": dtb_id,
                "group_id": group_id,  # Same group would also conflict
                "instructor_id": instructor_id,  # Same instructor
                "classroom_id": classroom_id,  # Same classroom would also conflict
            },
        )
        assert conflict_response.status_code == status.HTTP_409_CONFLICT
        assert "conflict" in conflict_response.json()["detail"].lower()

    def test_schedule_search_filters(self, authorized_client):
        """Test searching schedules with various filters."""
        # Would need to create test data first
        # Then test filtering by:
        # - subject
        # - instructor_id
        # - group_id
        # - classroom_id
        # - quarter_id
        # - day_id

        search_response = authorized_client.get(
            "/api/v1/scheduling/class-schedules",
            params={"subject": "Programming", "page": 1, "page_size": 10},
        )
        assert search_response.status_code == status.HTTP_200_OK
        data = search_response.json()["data"]
        assert "items" in data
        assert "total" in data
