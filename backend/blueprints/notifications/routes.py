import psycopg2.extras
from flask import jsonify
from flask_login import login_required, current_user

from blueprints.notifications import notifications_bp
from db.db import get_pg_connection


@notifications_bp.route("/api/notifications", methods=["GET"])
@login_required
def get_notifications():
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT notificationid, title, message, notif_type, is_read, related_id, created_at
            FROM notifications
            WHERE userid = %s
            ORDER BY created_at DESC
            LIMIT 50
            """,
            (current_user.userid,),
        )
        rows = cur.fetchall()
        result = []
        for r in rows:
            row = dict(r)
            if row.get("created_at"):
                row["created_at"] = row["created_at"].isoformat()
            result.append(row)
        return jsonify({"notifications": result}), 200
    except Exception as e:
        # Return empty list — never let a notification failure break the frontend
        return jsonify({"notifications": [], "error": str(e)}), 200
    finally:
        if conn:
            conn.close()


@notifications_bp.route("/api/notifications/<int:notif_id>/read", methods=["PATCH"])
@login_required
def mark_one_read(notif_id):
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE notifications SET is_read = TRUE WHERE notificationid = %s AND userid = %s",
            (notif_id, current_user.userid),
        )
        conn.commit()
        return jsonify({"message": "Marked as read"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@notifications_bp.route("/api/notifications/read-all", methods=["PATCH"])
@login_required
def mark_all_read():
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE notifications SET is_read = TRUE WHERE userid = %s",
            (current_user.userid,),
        )
        conn.commit()
        return jsonify({"message": "All marked as read"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
