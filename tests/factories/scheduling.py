"""Scheduling factories."""

from datetime import date, time, timedelta

import factory
from factory import fuzzy

from app.models.scheduling import (
    ClassSchedule,
    Day,
    DayTimeBlock,
    Quarter,
    Schedule,
    TimeBlock,
)


class ScheduleFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for Schedule model."""

    class Meta:
        model = Schedule
        sqlalchemy_session_persistence = "commit"

    name = fuzzy.FuzzyChoice(["Morning", "Afternoon", "Evening", "Night"])
    start_time = factory.LazyFunction(lambda: time(7, 0))
    end_time = factory.LazyFunction(lambda: time(13, 0))
    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")


class TimeBlockFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for TimeBlock model."""

    class Meta:
        model = TimeBlock
        sqlalchemy_session_persistence = "commit"

    start_time = factory.LazyFunction(lambda: time(8, 0))
    end_time = factory.LazyFunction(lambda: time(10, 0))
    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")


class DayFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for Day model."""

    class Meta:
        model = Day
        sqlalchemy_session_persistence = "commit"

    name = factory.Sequence(
        lambda n: [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ][n % 7]
    )
    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")


class DayTimeBlockFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for DayTimeBlock model."""

    class Meta:
        model = DayTimeBlock
        sqlalchemy_session_persistence = "commit"

    day = factory.SubFactory(DayFactory)
    time_block = factory.SubFactory(TimeBlockFactory)
    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")


class QuarterFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for Quarter model."""

    class Meta:
        model = Quarter
        sqlalchemy_session_persistence = "commit"

    start_date = factory.LazyFunction(date.today)
    end_date = factory.LazyAttribute(lambda obj: obj.start_date + timedelta(days=90))
    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")


class ClassScheduleFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for ClassSchedule model."""

    class Meta:
        model = ClassSchedule
        sqlalchemy_session_persistence = "commit"

    subject = factory.Faker("catch_phrase")
    quarter = factory.SubFactory(QuarterFactory)
    day_time_block = factory.SubFactory(DayTimeBlockFactory)
    group = factory.SubFactory("tests.factories.academic.StudentGroupFactory")
    instructor = factory.SubFactory("tests.factories.hr.InstructorFactory")
    classroom = factory.SubFactory("tests.factories.infrastructure.ClassroomFactory")
    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")
