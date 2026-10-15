from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Configure connection pooling parameters
engine_kwargs: dict[str, Any] = {"pool_pre_ping": True}
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
    })

# Database engine initialized with connection pool
engine = create_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

# Session factory bound to the engine
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a transactional SQLAlchemy Session per request.

    Guarantees session closure upon completion or exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
