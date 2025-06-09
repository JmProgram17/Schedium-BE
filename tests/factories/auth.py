"""Authentication factories."""

import factory
from factory import fuzzy

from app.core.security import SecurityUtils
from app.models.auth import Role, User


class RoleFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for Role model."""

    class Meta:
        model = Role
        sqlalchemy_session_persistence = "commit"

    name = factory.Sequence(lambda n: f"Role{n}")
    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for User model."""

    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    document_number = factory.Sequence(lambda n: f"1234567{n:02d}")
    password = factory.LazyFunction(lambda: SecurityUtils.get_password_hash("Test123!"))
    role = factory.SubFactory(RoleFactory)
    active = True
    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")
