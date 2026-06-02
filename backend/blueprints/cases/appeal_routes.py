from flask import jsonify, request
from flask_login import login_required

import psycopg2
import psycopg2.extras

from blueprints.cases import cases_bp
from db.db import get_pg_connection


# ==========================================================
# GET APPEALS
# ==========================================================
@cases_bp.route('/appeals', methods=['GET'])
@login_required
def get_appeals():

    conn = None

    try:

        conn = get_pg_connection()

        cur = conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        )

        cur.execute(
            """
            SELECT *
            FROM appeals
            ORDER BY appealid DESC
            """
        )

        appeals = cur.fetchall()

        return jsonify({
            "appeals": appeals
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if conn:
            conn.close()


# ==========================================================
# CREATE APPEAL
# ==========================================================
@cases_bp.route('/appeals', methods=['POST'])
@login_required
def create_appeal():

    data = request.get_json()

    caseid = data.get("caseid")
    reason = data.get("reason")

    conn = None

    try:

        conn = get_pg_connection()

        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO appeals
            (
                caseid,
                reason,
                status
            )
            VALUES
            (
                %s,
                %s,
                'Pending'
            )
            """,
            (
                caseid,
                reason
            )
        )

        conn.commit()

        return jsonify({
            "success": True,
            "message":
                "Appeal submitted successfully"
        }), 201

    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if conn:
            conn.close()


# ==========================================================
# APPEAL DECISION
# ==========================================================
@cases_bp.route(
    '/appealdecision',
    methods=['PUT']
)
@login_required
def appeal_decision():

    data = request.get_json()

    appealid = data.get("appealid")
    status = data.get("status")

    conn = None

    try:

        conn = get_pg_connection()

        cur = conn.cursor()

        cur.execute(
            """
            UPDATE appeals
            SET status=%s
            WHERE appealid=%s
            """,
            (
                status,
                appealid
            )
        )

        conn.commit()

        return jsonify({
            "success": True,
            "message":
                "Appeal updated successfully"
        })

    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if conn:
            conn.close()