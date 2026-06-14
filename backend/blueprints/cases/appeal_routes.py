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
            SELECT
                a.caseid,
                a.appealid,
                a.appealdate,
                a.appealstatus  AS status,
                a.decisiondate,
                a.decision,
                c.title         AS casename,
                (
                    SELECT ct2.courtname
                    FROM courtaccess ca2
                    JOIN court ct2 ON ct2.courtid = ca2.courtid
                    WHERE ca2.caseid = c.caseid
                    LIMIT 1
                ) AS courtname,
                (
                    SELECT TRIM(u2.firstname || ' ' || u2.lastname)
                    FROM caselawyeraccess cla2
                    JOIN lawyer lw2 ON lw2.lawyerid = cla2.lawyerid
                    JOIN users u2 ON u2.userid = lw2.userid
                    WHERE cla2.caseid = c.caseid
                    LIMIT 1
                ) AS lawyername,
                (
                    SELECT TRIM(u3.firstname || ' ' || u3.lastname)
                    FROM caseparticipantaccess cpa3
                    JOIN caseparticipant cp3 ON cp3.participantid = cpa3.participantid
                    JOIN users u3 ON u3.userid = cp3.userid
                    WHERE cpa3.caseid = c.caseid
                    LIMIT 1
                ) AS clientname
            FROM appeals a
            JOIN cases c ON c.caseid = a.caseid
            ORDER BY a.appealid DESC
            """
        )

        rows = cur.fetchall()

        appeals = []
        for row in rows:
            appeals.append({
                "caseid":      row["caseid"],
                "appealid":    row["appealid"],
                "appealdate":  row["appealdate"].isoformat() if row["appealdate"] else None,
                "status":      row["status"],
                "decisiondate": row["decisiondate"].isoformat() if row["decisiondate"] else None,
                "decision":    row["decision"],
                "casename":    row["casename"],
                "courtname":   row["courtname"],
                "lawyername":  row["lawyername"],
                "clientname":  row["clientname"],
            })

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
                appealstatus
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

    # appealId comes as a query param; body has appealStatus, decisionDate, decision
    appeal_id = request.args.get("appealId")
    appeal_status = data.get("appealStatus")
    decision_date = data.get("decisionDate")
    decision = data.get("decision")

    if not appeal_id:
        return jsonify({"error": "appealId query parameter is required"}), 400

    conn = None

    try:

        conn = get_pg_connection()

        cur = conn.cursor()

        cur.execute(
            """
            UPDATE appeals
            SET
                appealstatus = %s,
                decisiondate = %s,
                decision     = %s
            WHERE appealid = %s
            """,
            (
                appeal_status,
                decision_date or None,
                decision,
                appeal_id
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
