"""Human resources factories."""

import factory
from factory import fuzzy

from app.models.hr import Contract, Department, Instructor


class DepartmentFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for Department model."""

    class Meta:
        model = Department
        sqlalchemy_session_persistence = "commit"

    name = factory.Faker("company")
    phone_number = factory.Faker("phone_number")
    email = factory.Faker("company_email")
    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")


class ContractFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for Contract model."""

    class Meta:
        model = Contract
        sqlalchemy_session_persistence = "commit"

    contract_type = fuzzy.FuzzyChoice(
        ["Full Time", "Part Time", "Contract", "Temporary"]
    )
    hour_limit = fuzzy.FuzzyInteger(20, 48)
    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")


class InstructorFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for Instructor model."""

    class Meta:
        model = Instructor
        sqlalchemy_session_persistence = "commit"

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    phone_number = factory.Faker("phone_number")
    email = factory.Faker("email")
    hour_count = 0
    contract = factory.SubFactory(ContractFactory)
    department = factory.SubFactory(DepartmentFactory)
    active = True
    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")
