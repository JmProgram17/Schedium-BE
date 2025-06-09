"""Academic domain factories."""

from datetime import date, timedelta

import factory
from factory import fuzzy

from app.models.academic import Chain, Level, Nomenclature, Program, StudentGroup


class LevelFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for Level model."""

    class Meta:
        model = Level
        sqlalchemy_session_persistence = "commit"

    study_type = fuzzy.FuzzyChoice(["Technician", "Technologist", "Professional"])
    duration = fuzzy.FuzzyInteger(12, 48)


class NomenclatureFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for Nomenclature model."""

    class Meta:
        model = Nomenclature
        sqlalchemy_session_persistence = "commit"

    code = factory.Sequence(lambda n: f"NOM{n:03d}")
    description = factory.Faker("sentence")
    active = True


class ChainFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for Chain model."""

    class Meta:
        model = Chain
        sqlalchemy_session_persistence = "commit"

    name = factory.Faker("company")


class ProgramFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for Program model."""

    class Meta:
        model = Program
        sqlalchemy_session_persistence = "commit"

    name = factory.Faker("catch_phrase")
    nomenclature = factory.SubFactory(NomenclatureFactory)
    level = factory.SubFactory(LevelFactory)
    chain = factory.SubFactory(ChainFactory)
    department = factory.SubFactory("tests.factories.hr.DepartmentFactory")


class StudentGroupFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for StudentGroup model."""

    class Meta:
        model = StudentGroup
        sqlalchemy_session_persistence = "commit"

    group_number = factory.Sequence(lambda n: 2750000 + n)
    program = factory.SubFactory(ProgramFactory)
    start_date = factory.LazyFunction(date.today)
    end_date = factory.LazyAttribute(lambda obj: obj.start_date + timedelta(days=730))
    capacity = fuzzy.FuzzyInteger(20, 35)
    schedule = factory.SubFactory("tests.factories.scheduling.ScheduleFactory")
    active = True
