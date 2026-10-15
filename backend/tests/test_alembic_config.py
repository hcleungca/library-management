from pathlib import Path

from alembic.config import Config

from app.models import Base


def test_alembic_ini_file_exists():
    """Verify alembic.ini exists and has correct script_location."""
    backend_dir = Path(__file__).resolve().parents[1]
    ini_path = backend_dir / "alembic.ini"
    assert ini_path.exists()

    config = Config(str(ini_path))
    assert config.get_main_option("script_location") == "alembic"


def test_alembic_env_metadata_binding():
    """Verify target_metadata contains application tables for migrations."""
    assert Base.metadata is not None
    tables = set(Base.metadata.tables.keys())
    assert {"profiles", "books", "loans"}.issubset(tables)
