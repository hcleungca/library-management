from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from app.models.base import Base


def test_base_is_declarative_base():
    """Verify Base inherits from SQLAlchemy 2.0 DeclarativeBase."""
    assert issubclass(Base, DeclarativeBase)


def test_base_metadata_instance():
    """Verify Base has a valid MetaData instance for schema registry."""
    assert isinstance(Base.metadata, MetaData)

