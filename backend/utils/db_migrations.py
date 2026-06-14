"""
Lightweight startup migrations — add columns/tables that may be missing
from the initial DB schema without requiring a full migration tool.
Each function is idempotent (safe to run on every startup).
"""
import logging
from db.db import get_pg_connection

logger = logging.getLogger(__name__)


def ensure_documents_columns():
    """
    The documents table was originally created without uploaded_by or visibility.
    Add them if missing so the case-document upload/download endpoints work.
    """
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute("""
            ALTER TABLE documents
            ADD COLUMN IF NOT EXISTS uploaded_by INTEGER REFERENCES users(userid) ON DELETE SET NULL;
        """)
        cur.execute("""
            ALTER TABLE documents
            ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) NOT NULL DEFAULT 'court';
        """)
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.error("ensure_documents_columns failed: %s", exc)


def run_all():
    ensure_documents_columns()
