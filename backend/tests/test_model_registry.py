from sqlalchemy.orm import configure_mappers

from app.models import Base, Book, Loan, MaintenanceLog, Profile


def test_models_reexported():
    """Verify all ORM models are re-exported by app.models."""
    assert Base is not None
    assert Book is not None
    assert Loan is not None
    assert MaintenanceLog is not None
    assert Profile is not None


def test_metadata_tables_registered():
    """Verify all 4 model tables are discovered in Base.metadata."""
    tables = set(Base.metadata.tables.keys())
    expected = {"profiles", "books", "loans", "maintenance_logs"}
    assert expected.issubset(tables)


def test_mappers_configure_without_error():
    """Verify SQLAlchemy configure_mappers resolves all cross-model relationships."""
    configure_mappers()

    # Verify relationship mappers are resolved
    book_mapper = Book.__mapper__
    assert "loans" in book_mapper.relationships
    assert "maintenance_logs" in book_mapper.relationships

    loan_mapper = Loan.__mapper__
    assert "book" in loan_mapper.relationships
    assert "user" in loan_mapper.relationships

    profile_mapper = Profile.__mapper__
    assert "loans" in profile_mapper.relationships

    maintenance_mapper = MaintenanceLog.__mapper__
    assert "book" in maintenance_mapper.relationships

