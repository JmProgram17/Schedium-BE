"""Infrastructure factories."""

import factory
from factory import fuzzy

from app.models.infrastructure import Campus, Classroom, DepartmentClassroom
from tests.factories.hr import DepartmentFactory


class CampusFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for Campus model."""

    class Meta:
        model = Campus
        sqlalchemy_session_persistence = "commit"

    address = factory.Faker("address")
    phone_number = factory.Faker("phone_number")
    email = factory.Faker("email")
    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")


class ClassroomFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for Classroom model."""

    class Meta:
        model = Classroom
        sqlalchemy_session_persistence = "commit"

    room_number = factory.Sequence(lambda n: f"Room{n:03d}")
    capacity = fuzzy.FuzzyInteger(20, 50)
    campus = factory.SubFactory(CampusFactory)
    classroom_type = fuzzy.FuzzyChoice(
        ["Standard", "Laboratory", "Workshop", "Auditorium"]
    )
    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")


class DepartmentClassroomFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for DepartmentClassroom model."""

    class Meta:
        model = DepartmentClassroom
        sqlalchemy_session_persistence = "commit"

    department = factory.SubFactory(DepartmentFactory)
    classroom = factory.SubFactory(ClassroomFactory)
    priority = fuzzy.FuzzyInteger(0, 10)
    is_primary = factory.Faker("boolean")
    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")
