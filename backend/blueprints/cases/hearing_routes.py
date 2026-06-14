from flask import jsonify, request
from flask_login import login_required, current_user

import psycopg2
import psycopg2.extras

from blueprints.cases import cases_bp
from db.db import get_pg_connection


@cases_bp.route("/hearings", methods=["GET"])
@login_required
def get_hearings():
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        role = current_user.role
        userid = current_user.userid

        if role == "Judge":
            cur.execute(
                """
                SELECT h.hearingid, h.hearingdate, h.hearingtime, h.venue,
                       h.remarks, h.hearingstatus, c.caseid, c.title AS casename,
                       ct.courtname
                FROM hearings h
                JOIN cases c ON h.caseid = c.caseid
                JOIN judge j ON h.judgeid = j.judgeid
                LEFT JOIN courtaccess ca ON ca.caseid = c.caseid
                LEFT JOIN court ct ON ct.courtid = ca.courtid
                WHERE j.userid = %s
                ORDER BY h.hearingdate DESC
                """,
                (userid,),
            )
        elif role == "Lawyer":
            cur.execute(
                """
                SELECT h.hearingid, h.hearingdate, h.hearingtime, h.venue,
                       h.remarks, h.hearingstatus, c.caseid, c.title AS casename,
                       ct.courtname
                FROM hearings h
                JOIN cases c ON h.caseid = c.caseid
                JOIN caselawyeraccess cla ON cla.caseid = c.caseid
                JOIN lawyer l ON l.lawyerid = cla.lawyerid
                LEFT JOIN courtaccess ca ON ca.caseid = c.caseid
                LEFT JOIN court ct ON ct.courtid = ca.courtid
                WHERE l.userid = %s
                ORDER BY h.hearingdate DESC
                """,
                (userid,),
            )
        elif role == "CaseParticipant":
            cur.execute(
                """
                SELECT h.hearingid, h.hearingdate, h.hearingtime, h.venue,
                       h.remarks, h.hearingstatus, c.caseid, c.title AS casename,
                       ct.courtname
                FROM hearings h
                JOIN cases c ON h.caseid = c.caseid
                JOIN caseparticipantaccess cpa ON cpa.caseid = c.caseid
                JOIN caseparticipant cp ON cp.participantid = cpa.participantid
                LEFT JOIN courtaccess ca ON ca.caseid = c.caseid
                LEFT JOIN court ct ON ct.courtid = ca.courtid
                WHERE cp.userid = %s
                ORDER BY h.hearingdate DESC
                """,
                (userid,),
            )
        else:
            cur.execute(
                """
                SELECT h.hearingid, h.hearingdate, h.hearingtime, h.venue,
                       h.remarks, h.hearingstatus, c.caseid, c.title AS casename,
                       ct.courtname
                FROM hearings h
                JOIN cases c ON h.caseid = c.caseid
                LEFT JOIN courtaccess ca ON ca.caseid = c.caseid
                LEFT JOIN court ct ON ct.courtid = ca.courtid
                ORDER BY h.hearingdate DESC
                """
            )

        rows = cur.fetchall()
        result = []
        for hearing in rows:
            result.append({
                "hearingid": hearing["hearingid"],
                "id": hearing["hearingid"],
                "caseid": hearing.get("caseid"),
                "casename": hearing.get("casename") or hearing.get("title"),
                "casetitle": hearing.get("casename") or hearing.get("title"),
                "courtname": hearing.get("courtname") or hearing.get("venue") or "N/A",
                "hearingdate": (
                    hearing["hearingdate"].isoformat()
                    if hearing["hearingdate"]
                    else None
                ),
                "hearingtime": (
                    hearing["hearingtime"].strftime("%H:%M")
                    if hearing["hearingtime"]
                    else None
                ),
                "venue": hearing.get("venue"),
                "remarks": hearing.get("remarks") or "",
                "hearingstatus": hearing.get("hearingstatus") or "scheduled",
            })

        return jsonify({"hearings": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@cases_bp.route("/hearings", methods=["POST"])
@login_required
def schedule_hearing():
    data = request.get_json() or {}
    casetitle = data.get("casetitle") or data.get("caseTitle")
    hearingdate = data.get("hearingdate") or data.get("hearingDate")
    hearingtime = data.get("hearingtime") or data.get("hearingTime")
    remarks = data.get("remarks")

    if not all([casetitle, hearingdate, hearingtime]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("SELECT judgeid FROM judge WHERE userid = %s", (current_user.userid,))
        judge_row = cur.fetchone()
        if not judge_row:
            return jsonify({"error": "Judge profile not found"}), 404
        judgeid = judge_row[0]

        cur.execute(
            "SELECT caseid FROM cases WHERE title = %s LIMIT 1",
            (casetitle,),
        )
        case_row = cur.fetchone()
        if not case_row:
            return jsonify({
                "error": f'Case "{casetitle}" not found. Use an existing case title.',
            }), 404
        caseid = case_row[0]

        cur.execute(
            "SELECT hearingid, hearingdate FROM hearings WHERE caseid = %s AND hearingstatus = 'scheduled' LIMIT 1",
            (caseid,),
        )
        existing_hearing = cur.fetchone()
        if existing_hearing:
            return jsonify({
                "error": "A hearing is already scheduled for this case",
                "hearingid": existing_hearing[0],
                "hearingdate": existing_hearing[1].isoformat() if existing_hearing[1] else None,
            }), 409

        cur.execute(
            "SELECT COALESCE(MAX(hearingid), 0) + 1 FROM hearings"
        )
        next_hid = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO hearings (caseid, hearingid, judgeid, hearingdate, hearingtime, remarks)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (caseid, next_hid, judgeid, hearingdate, hearingtime, remarks),
        )
        conn.commit()

        # Notify lawyers and clients on the case
        try:
            from utils.notifications import push_notification
            cur.execute(
                "SELECT l.userid FROM lawyer l JOIN caselawyeraccess cla ON cla.lawyerid = l.lawyerid WHERE cla.caseid = %s",
                (caseid,),
            )
            for row in cur.fetchall():
                push_notification(row[0], "Hearing Scheduled",
                    f'A hearing has been scheduled for case "{casetitle}" on {hearingdate}.', "info", caseid)
            cur.execute(
                "SELECT cp.userid FROM caseparticipant cp JOIN caseparticipantaccess cpa ON cpa.participantid = cp.participantid WHERE cpa.caseid = %s",
                (caseid,),
            )
            for row in cur.fetchall():
                push_notification(row[0], "Hearing Scheduled",
                    f'A hearing has been scheduled for your case "{casetitle}" on {hearingdate}.', "info", caseid)
        except Exception:
            pass

        return jsonify({"message": "Hearing scheduled successfully"}), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@cases_bp.route("/hearings/remarks", methods=["PUT"])
@login_required
def update_hearing_remarks():
    hearing_id = request.args.get("hearingid")
    if not hearing_id:
        return jsonify({"error": "hearingid query parameter is required"}), 400

    data = request.get_json() or {}
    remarks = data.get("remarks")
    if remarks is None:
        return jsonify({"error": "remarks field is required in JSON body"}), 400

    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE hearings SET remarks = %s WHERE hearingid = %s",
            (remarks, hearing_id),
        )
        if cur.rowcount == 0:
            return jsonify({"error": "Hearing not found"}), 404
        conn.commit()
        return jsonify({"message": "Remarks updated successfully"}), 200
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@cases_bp.route("/hearings/<int:hearing_id>/status", methods=["PATCH"])
@login_required
def update_hearing_status(hearing_id):
    if current_user.role not in ("CourtRegistrar", "Judge", "Admin"):
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json() or {}
    new_status = data.get("status", "").strip()
    valid_statuses = ["scheduled", "completed", "adjourned", "cancelled"]
    if new_status.lower() not in valid_statuses:
        return jsonify({"error": f"Status must be one of: {', '.join(valid_statuses)}"}), 400

    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE hearings SET hearingstatus = %s WHERE hearingid = %s",
            (new_status.lower(), hearing_id),
        )
        if cur.rowcount == 0:
            return jsonify({"error": "Hearing not found"}), 404
        conn.commit()

        # Notify lawyers and clients on the case
        try:
            from utils.notifications import push_notification
            cur.execute("SELECT caseid FROM hearings WHERE hearingid = %s", (hearing_id,))
            h = cur.fetchone()
            if h:
                cid = h[0]
                label = new_status.capitalize()
                cur.execute(
                    "SELECT l.userid FROM lawyer l JOIN caselawyeraccess cla ON cla.lawyerid = l.lawyerid WHERE cla.caseid = %s",
                    (cid,),
                )
                for row in cur.fetchall():
                    push_notification(row[0], "Hearing Updated",
                        f"A hearing status has been updated to {label}.", "info", hearing_id)
                cur.execute(
                    "SELECT cp.userid FROM caseparticipant cp JOIN caseparticipantaccess cpa ON cpa.participantid = cp.participantid WHERE cpa.caseid = %s",
                    (cid,),
                )
                for row in cur.fetchall():
                    push_notification(row[0], "Hearing Updated",
                        f"The status of a hearing on your case has been updated to {label}.", "info", hearing_id)
        except Exception:
            pass

        return jsonify({"message": "Hearing status updated"}), 200
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@cases_bp.route(
    '/hearings/addvenue',
    methods=['PUT']
)
@login_required
def add_hearing_venue():

    data = request.get_json()

    hearing_id = data.get("hearingid")
    venue = data.get("venue")

    if not hearing_id:
        return jsonify({
            "success": False,
            "message": "hearingid required"
        }), 400

    conn = None

    try:

        conn = get_pg_connection()

        cur = conn.cursor()

        cur.execute(
            """
            UPDATE hearings
            SET venue=%s
            WHERE hearingid=%s
            """,
            (
                venue,
                hearing_id
            )
        )

        conn.commit()

        return jsonify({
            "success": True,
            "message":
                "Venue updated successfully"
        })

    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if conn:
            conn.close()