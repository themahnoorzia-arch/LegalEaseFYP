"""Utility for writing entries to logtable without crashing the caller."""
import logging

logger = logging.getLogger(__name__)


def write_log(action_type: str, description: str, entity_type: str, status: str = "Success"):
    """
    Insert one row into logtable.
    Fire-and-forget: any exception is swallowed so a log failure never
    breaks the actual request that triggered it.
    """
    try:
        from db.db import get_pg_connection
        conn = get_pg_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO logtable (actiontype, description, status, entitytype)
                VALUES (%s, %s, %s, %s)
                """,
                (action_type, description, status, entity_type),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as exc:
        logger.warning("write_log failed (non-fatal): %s", exc)
