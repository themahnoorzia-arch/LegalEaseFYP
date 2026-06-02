"""
db/db.py
--------
Central database access layer.

Provides:
  - SQLAlchemy engine + ORM session factory  (used via get_db())
  - Raw psycopg2 connection factory           (used via get_pg_connection())
  - Flask teardown helpers                    (register_teardowns)
  - Context-manager wrappers for safe usage   (orm_session, pg_connection)

Compatibility guarantee
-----------------------
All names that exist in the current app.py are re-exported unchanged:

    engine          – SQLAlchemy Engine
    SessionLocal    – SQLAlchemy sessionmaker
    get_pg_connection() – returns a raw psycopg2 connection

New additions are purely additive and do not break existing call-sites.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection as PgConnection

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from config import Config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engine — created once at import time, shared across the entire application.
# pool_pre_ping=True lets SQLAlchemy silently recycle stale connections that
# were dropped by Supabase / pgBouncer after an idle timeout.
# ---------------------------------------------------------------------------
engine: Engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,          # health-check connections before use
    pool_size=10,                # base pool; tune via env if needed
    max_overflow=20,             # extra connections under burst load
    pool_timeout=30,             # seconds to wait for a free slot
    pool_recycle=1800,           # recycle connections every 30 min
    echo=False,                  # set True (or use logging) for SQL debug
)

# ---------------------------------------------------------------------------
# ORM session factory — mirrors the original SessionLocal in app.py exactly.
# ---------------------------------------------------------------------------
SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ---------------------------------------------------------------------------
# Optional: log slow queries in development.
# Activate by setting SQLALCHEMY_ECHO=slow in your env / Config.
# ---------------------------------------------------------------------------
@event.listens_for(engine, "before_cursor_execute")
def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(
        __import__("time").monotonic()
    )


@event.listens_for(engine, "after_cursor_execute")
def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    elapsed = __import__("time").monotonic() - conn.info["query_start_time"].pop()
    if elapsed > 1.0:  # warn if query takes longer than 1 second
        logger.warning("Slow query (%.3fs): %.200s", elapsed, statement)


# ---------------------------------------------------------------------------
# Raw psycopg2 connection — preserves the exact signature from app.py so that
# every existing call-site (get_pg_connection()) continues to work unchanged.
# ---------------------------------------------------------------------------
def get_pg_connection() -> PgConnection:
    """
    Return a raw psycopg2 connection.

    The caller is responsible for calling conn.close() — or, preferably,
    use the pg_connection() context manager instead which handles cleanup
    and rollback automatically.
    """
    return psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)


# ---------------------------------------------------------------------------
# ORM session dependency — use this in new blueprint routes.
#
# Usage (Flask route):
#   db = get_db()
#   try:
#       result = db.query(MyModel).all()
#       db.commit()
#   except Exception:
#       db.rollback()
#       raise
#   finally:
#       db.close()
#
# Or use the orm_session() context manager below for cleaner code.
# ---------------------------------------------------------------------------
def get_db() -> Session:
    """
    Return a new SQLAlchemy ORM Session.

    Mirrors the ``db = SessionLocal()`` pattern used throughout app.py.
    The caller must call db.close() in a finally block.
    For new code, prefer the orm_session() context manager.
    """
    return SessionLocal()


# ---------------------------------------------------------------------------
# Context managers — preferred for new/refactored code.
# ---------------------------------------------------------------------------
@contextmanager
def orm_session() -> Generator[Session, None, None]:
    """
    Context manager that yields an ORM Session and handles
    commit / rollback / close automatically.

    Usage:
        with orm_session() as db:
            db.add(obj)
            # commit happens automatically on clean exit
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("ORM session rolled back due to error: %s", exc)
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("ORM session rolled back due to unexpected error: %s", exc)
        raise
    finally:
        db.close()


@contextmanager
def pg_connection(
    cursor_factory=psycopg2.extras.RealDictCursor,
) -> Generator[PgConnection, None, None]:
    """
    Context manager that yields a raw psycopg2 connection and handles
    commit / rollback / close automatically.

    Usage:
        with pg_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")

    Pass cursor_factory=None to get the default tuple cursor.
    """
    conn: PgConnection = psycopg2.connect(
        Config.SQLALCHEMY_DATABASE_URI,
        cursor_factory=cursor_factory,
    )
    try:
        yield conn
        conn.commit()
    except psycopg2.Error as exc:
        conn.rollback()
        logger.exception("psycopg2 connection rolled back due to error: %s", exc)
        raise
    except Exception as exc:
        conn.rollback()
        logger.exception(
            "psycopg2 connection rolled back due to unexpected error: %s", exc
        )
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Flask teardown registration — call once inside create_app().
#
# Usage in app factory:
#   from db.db import register_teardowns
#   register_teardowns(app)
# ---------------------------------------------------------------------------
def register_teardowns(app) -> None:
    """
    Register SQLAlchemy engine disposal on app teardown.
    Call this once from your Flask application factory.
    """

    @app.teardown_appcontext
    def shutdown_session(exception=None):  # noqa: ANN001
        """Close any ORM sessions bound to Flask's g at end of each request."""
        from flask import g  # local import to avoid circular refs at module load

        db: Session | None = g.pop("db", None)
        if db is not None:
            if exception:
                db.rollback()
            db.close()


# ---------------------------------------------------------------------------
# Health-check utility — useful for /api/health endpoints or startup checks.
# ---------------------------------------------------------------------------
def check_db_connection() -> bool:
    """
    Return True if the database is reachable, False otherwise.
    Safe to call from a health-check route.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        return False