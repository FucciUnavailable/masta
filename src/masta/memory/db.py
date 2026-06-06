"""SQLite engine/session management via SQLModel.

The database lives under the configured data dir (``~/.local/share/masta/masta.db`` by
default). Tests pass an in-memory or temp path.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from masta.config import get_settings

_engine = None


def _engine_for(db_path: Path | None):
    if db_path is None:
        db_path = get_settings().db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_db(db_path: Path | None = None):
    """Create tables (idempotent) and return the engine.

    Cached as the module-level engine when using the default path.
    """
    global _engine
    # Import models module so all table classes are registered on SQLModel.metadata
    # before create_all runs.
    import masta.memory.models  # noqa: F401

    engine = _engine_for(db_path)
    SQLModel.metadata.create_all(engine)
    if db_path is None:
        _engine = engine
    return engine


@contextmanager
def get_session(db_path: Path | None = None) -> Iterator[Session]:
    """Yield a session, initializing the database on first use."""
    global _engine
    engine = _engine if (_engine is not None and db_path is None) else init_db(db_path)
    with Session(engine) as session:
        yield session
