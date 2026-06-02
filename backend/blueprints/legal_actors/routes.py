from flask import jsonify, request
from flask_login import login_required, current_user

import psycopg2
import psycopg2.extras

from db.db import get_pg_connection, SessionLocal
from models import Judge

from blueprints.legal_actors import legal_actors_bp

@legal_actors_bp.route('/judges', methods=['GET'])
@login_required
def get_judges_for_court():
    conn = None
    try:
        conn = get_pg_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "SELECT courtid FROM courtregistrar WHERE userid = %s",
                (current_user.userid,),
            )
            court = cur.fetchone()
            if not court:
                return jsonify({"judges": []}), 200

            cur.execute(
                """
                SELECT j.judgeid, u.firstname, u.lastname, j.position,
                       j.expyears, j.appointmentdate, j.specialization
                FROM judge j
                JOIN users u ON u.userid = j.userid
                JOIN judgeworksin jw ON jw.judgeid = j.judgeid
                WHERE jw.courtid = %s
                """,
                (court["courtid"],),
            )
            judges = cur.fetchall()

            response = []
            for judge in judges:
                cur.execute(
                    """
                    SELECT c.title
                    FROM judgeaccess ja
                    JOIN cases c ON ja.caseid = c.caseid
                    WHERE ja.judgeid = %s
                    """,
                    (judge["judgeid"],),
                )
                assigned_titles = [c["title"] for c in cur.fetchall()]
                response.append(
                    {
                        "judgeid": judge["judgeid"],
                        "name": f"{judge['firstname']} {judge['lastname']}",
                        "position": judge["position"],
                        "expyears": judge["expyears"],
                        "appointmentdate": (
                            judge["appointmentdate"].isoformat()
                            if judge["appointmentdate"]
                            else None
                        ),
                        "specialization": judge["specialization"],
                        "assigned_cases": assigned_titles,
                    }
                )
        return jsonify({"judges": response})
    finally:
        if conn:
            conn.close()


@legal_actors_bp.route('/judge', methods=['PUT'])
@login_required
def update_judge():

    data = request.get_json()

    if not data:
        return jsonify(
            success=False,
            message="No data provided"
        ), 400

    full_name = data.get("name", "").strip()

    if not full_name:
        return jsonify(
            success=False,
            message="Judge name is required"
        ), 400

    parts = full_name.split()

    firstname = parts[0]
    lastname = " ".join(parts[1:])

    conn = None

    try:

        conn = get_pg_connection()

        cur = conn.cursor(
            cursor_factory=psycopg2.extras.DictCursor
        )

        cur.execute(
            """
            SELECT userid
            FROM users
            WHERE firstname=%s
            AND lastname=%s
            """,
            (firstname, lastname)
        )

        user_row = cur.fetchone()

        if not user_row:
            return jsonify(
                success=False,
                message="Judge not found"
            ), 404

        userid = user_row["userid"]

        cur.execute(
            """
            SELECT *
            FROM judge
            WHERE userid=%s
            """,
            (userid,)
        )

        judge = cur.fetchone()

        if not judge:
            return jsonify(
                success=False,
                message="Judge profile not found"
            ), 404

        cur.execute(
            """
            UPDATE judge
            SET
                specialization=%s,
                appointmentdate=%s,
                expyears=%s,
                position=%s
            WHERE userid=%s
            """,
            (
                data.get(
                    "specialization",
                    judge["specialization"]
                ),
                data.get(
                    "appointmentDate",
                    judge["appointmentdate"]
                ),
                data.get(
                    "experience",
                    judge["expyears"]
                ),
                data.get(
                    "position",
                    judge["position"]
                ),
                userid
            )
        )

        conn.commit()

        return jsonify(
            success=True,
            message="Profile updated successfully"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify(
            success=False,
            message=str(e)
        ), 500

    finally:

        if conn:
            conn.close()

# ==========================================================
# GET PROSECUTORS
# ==========================================================
@legal_actors_bp.route('/prosecutors', methods=['GET'])
@login_required
def get_prosecutors():

    conn = None

    try:

        conn = get_pg_connection()

        with conn.cursor(
            cursor_factory=psycopg2.extras.DictCursor
        ) as cur:

            cur.execute(
                """
                SELECT courtid
                FROM courtregistrar
                WHERE userid=%s
                """,
                (current_user.userid,)
            )

            row = cur.fetchone()

            if not row:
                return jsonify({
                    "error": "Registrar not found"
                }), 404

            court_id = row["courtid"]

            cur.execute(
                """
                SELECT *
                FROM prosecutor
                """
            )

            prosecutors = cur.fetchall()

            cur.execute(
                """
                SELECT
                    p.prosecutorid,
                    c.title
                FROM prosecutorassign pa
                JOIN prosecutor p
                    ON pa.prosecutorid = p.prosecutorid
                JOIN cases c
                    ON pa.caseid = c.caseid
                JOIN courtaccess ca
                    ON ca.caseid = c.caseid
                WHERE ca.courtid = %s
                """,
                (court_id,)
            )

            assignments = cur.fetchall()

        prosecutor_case_map = {}

        for row in assignments:

            pid = row["prosecutorid"]

            prosecutor_case_map.setdefault(
                pid,
                []
            ).append(
                row["title"]
            )

        result = []

        for p in prosecutors:

            assigned = prosecutor_case_map.get(
                p["prosecutorid"],
                []
            )

            result.append({
                "id": p["prosecutorid"],
                "name": p["name"],
                "experience": p["experience"],
                "status": p["status"],
                "assignedCases": assigned
            })

        return jsonify({
            "prosecutors": result
        }), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if conn:
            conn.close()


# ==========================================================
# CREATE PROSECUTOR
# ==========================================================
@legal_actors_bp.route('/prosecutor', methods=['POST'])
@login_required
def create_prosecutor():

    data = request.get_json()

    name = data.get('name')
    experience = data.get('experience')
    status = data.get('status')
    case_names = data.get('case_names', [])

    if not name or experience is None or status is None:
        return jsonify({
            "error": "Missing required fields"
        }), 400

    conn = None

    try:

        conn = get_pg_connection()

        cur = conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        )

        cur.execute(
            """
            INSERT INTO prosecutor
            (
                name,
                experience,
                status
            )
            VALUES (%s,%s,%s)
            RETURNING prosecutorid
            """,
            (
                name,
                experience,
                status
            )
        )

        prosecutor_row = cur.fetchone()

        prosecutor_id = prosecutor_row["prosecutorid"]

        if case_names:

            cur.execute(
                """
                SELECT caseid
                FROM cases
                WHERE title = ANY(%s)
                """,
                (case_names,)
            )

            case_rows = cur.fetchall()

            for row in case_rows:

                cur.execute(
                    """
                    INSERT INTO prosecutorassign
                    (
                        prosecutorid,
                        caseid
                    )
                    VALUES (%s,%s)
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        prosecutor_id,
                        row["caseid"]
                    )
                )

        conn.commit()

        return jsonify({
            "id": prosecutor_id,
            "name": name,
            "experience": experience,
            "status": status,
            "assigned_cases": case_names
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
# UPDATE PROSECUTOR
# ==========================================================
@legal_actors_bp.route('/prosecutor', methods=['PUT'])
@login_required
def update_prosecutor():

    data = request.get_json()

    prosecutor_id = data.get('id')
    name = data.get('name')
    experience = data.get('experience')
    status = data.get('status')
    case_names = data.get('case_names', [])

    if not prosecutor_id or not name:
        return jsonify({
            "error": "Missing required fields"
        }), 400

    conn = None

    try:

        conn = get_pg_connection()

        cur = conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        )

        cur.execute(
            """
            UPDATE prosecutor
            SET
                name=%s,
                experience=%s,
                status=%s
            WHERE prosecutorid=%s
            """,
            (
                name,
                experience,
                status,
                prosecutor_id
            )
        )

        cur.execute(
            """
            DELETE FROM prosecutorassign
            WHERE prosecutorid=%s
            """,
            (prosecutor_id,)
        )

        if case_names:

            cur.execute(
                """
                SELECT caseid
                FROM cases
                WHERE title = ANY(%s)
                """,
                (case_names,)
            )

            case_rows = cur.fetchall()

            for row in case_rows:

                cur.execute(
                    """
                    INSERT INTO prosecutorassign
                    (
                        prosecutorid,
                        caseid
                    )
                    VALUES (%s,%s)
                    """,
                    (
                        prosecutor_id,
                        row["caseid"]
                    )
                )

        conn.commit()

        return jsonify({
            "success": True,
            "message":
                "Prosecutor updated successfully"
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


# ==========================================================
# DELETE PROSECUTOR
# ==========================================================
@legal_actors_bp.route(
    '/prosecutor/<int:prosecutor_id>',
    methods=['DELETE']
)
@login_required
def delete_prosecutor(prosecutor_id):

    conn = None

    try:

        conn = get_pg_connection()

        cur = conn.cursor()

        cur.execute(
            """
            DELETE FROM prosecutorassign
            WHERE prosecutorid=%s
            """,
            (prosecutor_id,)
        )

        cur.execute(
            """
            DELETE FROM prosecutor
            WHERE prosecutorid=%s
            """,
            (prosecutor_id,)
        )

        conn.commit()

        return jsonify({
            "success": True,
            "message":
                "Prosecutor deleted successfully"
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