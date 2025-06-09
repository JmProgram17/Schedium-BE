"""
Integration tests for complex transactions.
"""

from datetime import date, time

import pytest
from sqlalchemy.exc import IntegrityError

from app.schemas.scheduling import ClassScheduleCreate
from app.services.academic import AcademicService
from app.services.hr import HRService
from app.services.scheduling import SchedulingService


class TestComplexTransactions:
    """Test complex multi-table transactions."""

    def test_create_complete_class_schedule(self, db_session, test_program):
        """Test creating a complete class schedule with all dependencies."""
        # Services
        academic_service = AcademicService(db_session)
        hr_service = HRService(db_session)
        scheduling_service = SchedulingService(db_session)

        # Create all required entities

        # 1. Department
        department = hr_service.create_department(
            {"name": "Test Department", "email": "dept@test.com"}
        )

        # 2. Contract
        contract = hr_service.create_contract(
            {"contract_type": "Full Time", "hour_limit": 40}
        )

        # 3. Instructor
        instructor = hr_service.create_instructor(
            {
                "first_name": "Test",
                "last_name": "Instructor",
                "email": "instructor@test.com",
                "contract_id": contract.contract_id,
                "department_id": department.department_id,
            }
        )

        # 4. Campus
        from app.services.infrastructure import InfrastructureService

        infra_service = InfrastructureService(db_session)

        campus = infra_service.create_campus(
            {"address": "123 Test Street", "email": "campus@test.com"}
        )

        # 5. Classroom
        classroom = infra_service.create_classroom(
            {"room_number": "A101", "capacity": 30, "campus_id": campus.campus_id}
        )

        # 6. Schedule
        schedule = scheduling_service.create_schedule(
            {"name": "Morning", "start_time": time(7, 0), "end_time": time(13, 0)}
        )

        # 7. Student Group
        group = academic_service.create_student_group(
            {
                "group_number": 2750123,
                "program_id": test_program.program_id,
                "start_date": date(2024, 1, 1),
                "end_date": date(2025, 12, 31),
                "capacity": 25,
                "schedule_id": schedule.schedule_id,
            }
        )

        # 8. Quarter
        quarter = scheduling_service.create_quarter(
            {"start_date": date(2024, 1, 1), "end_date": date(2024, 3, 31)}
        )

        # 9. Time Block
        time_block = scheduling_service.create_time_block(
            {"start_time": time(8, 0), "end_time": time(10, 0)}
        )

        # 10. Day
        days = scheduling_service.get_days()
        monday = next(d for d in days if d.name == "Monday")

        # 11. Day-Time Block
        day_time_block = scheduling_service.create_day_time_block(
            {"day_id": monday.day_id, "time_block_id": time_block.time_block_id}
        )

        # Finally, create class schedule
        class_schedule = scheduling_service.create_class_schedule(
            {
                "subject": "Programming 101",
                "quarter_id": quarter.quarter_id,
                "day_time_block_id": day_time_block.day_time_block_id,
                "group_id": group.group_id,
                "instructor_id": instructor.instructor_id,
                "classroom_id": classroom.classroom_id,
            }
        )

        # Verify all relationships
        assert class_schedule.subject == "Programming 101"
        assert class_schedule.instructor.instructor_id == instructor.instructor_id
        assert class_schedule.classroom.classroom_id == classroom.classroom_id
        assert class_schedule.group.group_id == group.group_id

        # Verify instructor hours were updated
        updated_instructor = hr_service.get_instructor(instructor.instructor_id)
        assert float(updated_instructor.hour_count) > 0

    def test_transaction_rollback_on_conflict(self, db_session, test_program):
        """Test that entire transaction rolls back on conflict."""
        scheduling_service = SchedulingService(db_session)

        # Create initial data
        quarter = scheduling_service.create_quarter(
            {"start_date": date(2024, 4, 1), "end_date": date(2024, 6, 30)}
        )

        initial_quarter_count = len(
            scheduling_service.get_quarters({"page": 1, "page_size": 100}).items
        )

        try:
            # Try to create overlapping quarter (should fail)
            scheduling_service.create_quarter(
                {
                    "start_date": date(2024, 5, 1),  # Overlaps
                    "end_date": date(2024, 7, 31),
                }
            )
        except Exception:
            db_session.rollback()

        # Verify no new quarter was created
        final_quarter_count = len(
            scheduling_service.get_quarters({"page": 1, "page_size": 100}).items
        )

        assert final_quarter_count == initial_quarter_count
