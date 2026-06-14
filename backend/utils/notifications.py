"""
Push in-app notifications to users.
Never raises — failures are logged silently so notifications never break the main request.
"""
import logging
from db.db import get_pg_connection

logger = logging.getLogger(__name__)

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS notifications (
    notificationid SERIAL PRIMARY KEY,
    userid         INTEGER NOT NULL,
    title          VARCHAR(255) NOT NULL,
    message        TEXT,
    notif_type     VARCHAR(50) DEFAULT 'info',
    is_read        BOOLEAN DEFAULT FALSE,
    related_id     INTEGER,
    created_at     TIMESTAMP DEFAULT NOW()
);
"""


def ensure_notifications_table():
    """Create the notifications table if it doesn't exist. Call once at app startup."""
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute(_CREATE_TABLE_SQL)
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.error("Could not create notifications table: %s", exc)


def push_notification(userid, title, message, notif_type="info", related_id=None):
    """Insert a notification row for a user. Silently swallows all errors."""
    if not userid:
        return
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO notifications (userid, title, message, notif_type, related_id)
               VALUES (%s, %s, %s, %s, %s)""",
            (userid, title, message, notif_type, related_id),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.error("push_notification failed for user %s: %s", userid, exc)
