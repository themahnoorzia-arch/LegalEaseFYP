"""Admin-only API routes."""
import psycopg2.extras
from flask import jsonify, request
from flask_login import login_required, current_user

from blueprints.users import users_bp
from db.db import get_pg_connection


def _require_admin():
    if current_user.role != "Admin":
        return jsonify({"error": "Admin access required"}), 403
    return None


# ── Stats overview ──────────────────────────────────────────────────────────

@users_bp.route("/api/admin/stats", methods=["GET"])
@login_required
def admin_stats():
    err = _require_admin()
    if err:
        return err
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("SELECT COUNT(*) AS total FROM cases")
        total_cases = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) AS total FROM cases WHERE status = 'Open'")
        open_cases = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) AS total FROM cases WHERE status = 'Pending'")
        pending_cases = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) AS total FROM cases WHERE status = 'Closed'")
        closed_cases = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) AS total FROM users")
        total_users = cur.fetchone()["total"]

        cur.execute("SELECT role, COUNT(*) AS cnt FROM users GROUP BY role ORDER BY role")
        users_by_role = {r["role"]: r["cnt"] for r in cur.fetchall()}

        cur.execute("SELECT COUNT(*) AS total FROM hearings")
        total_hearings = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) AS total FROM appeals")
        total_appeals = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) AS total FROM appeals WHERE appealstatus = 'Pending'")
        pending_appeals = cur.fetchone()["total"]

        return jsonify({
            "cases": {
                "total": total_cases,
                "open": open_cases,
                "pending": pending_cases,
                "closed": closed_cases,
            },
            "users": {
                "total": total_users,
                "by_role": users_by_role,
            },
            "hearings": {"total": total_hearings},
            "appeals": {"total": total_appeals, "pending": pending_appeals},
        }), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if conn:
            conn.close()


# ── User management ─────────────────────────────────────────────────────────

@users_bp.route("/api/admin/users", methods=["GET"])
@login_required
def admin_list_users():
    err = _require_admin()
    if err:
        return err
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT
                u.userid, u.firstname, u.lastname, u.email,
                u.phoneno, u.cnic, u.role, u.createdat,
                CASE
                    WHEN u.role = 'Judge' THEN
                        (SELECT j.specialization FROM judge j WHERE j.userid = u.userid LIMIT 1)
                    WHEN u.role = 'Lawyer' THEN
                        (SELECT l.specialization FROM lawyer l WHERE l.userid = u.userid LIMIT 1)
                    ELSE NULL
                END AS specialization
            FROM users u
            ORDER BY u.createdat DESC NULLS LAST, u.userid DESC
            """
        )
        rows = cur.fetchall()
        result = []
        for r in rows:
            result.append({
                "userid":         r["userid"],
                "name":           f"{r['firstname'] or ''} {r['lastname'] or ''}".strip(),
                "firstname":      r["firstname"],
                "lastname":       r["lastname"],
                "email":          r["email"] or "—",
                "phone":          r["phoneno"] or "—",
                "cnic":           r["cnic"] or "—",
                "role":           r["role"],
                "specialization": r["specialization"] or "—",
                "joinedAt":       r["createdat"].isoformat() if r["createdat"] else None,
            })
        return jsonify({"users": result}), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if conn:
            conn.close()


@users_bp.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@login_required
def admin_delete_user(user_id):
    err = _require_admin()
    if err:
        return err
    if user_id == current_user.userid:
        return jsonify({"error": "Cannot delete your own account"}), 400
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT firstname, lastname, role FROM users WHERE userid = %s", (user_id,))
        user = cur.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404
        cur.execute("DELETE FROM users WHERE userid = %s", (user_id,))
        conn.commit()

        from utils.logging import write_log
        write_log(
            "DELETE",
            f"Admin deleted user: {user['firstname']} {user['lastname']} ({user['role']})",
            "user",
        )
        return jsonify({"message": "User deleted"}), 200
    except Exception as exc:
        if conn:
            conn.rollback()
        return jsonify({"error": str(exc)}), 500
    finally:
        if conn:
            conn.close()


@users_bp.route("/api/admin/users/<int:user_id>/role", methods=["PATCH"])
@login_required
def admin_change_role(user_id):
    err = _require_admin()
    if err:
        return err
    data = request.get_json() or {}
    new_role = data.get("role", "").strip()
    valid_roles = ["Admin", "CourtRegistrar", "CaseParticipant", "Lawyer", "Judge"]
    if new_role not in valid_roles:
        return jsonify({"error": f"Invalid role. Must be one of: {', '.join(valid_roles)}"}), 400
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "UPDATE users SET role = %s WHERE userid = %s RETURNING firstname, lastname",
            (new_role, user_id),
        )
        updated = cur.fetchone()
        if not updated:
            return jsonify({"error": "User not found"}), 404
        conn.commit()

        from utils.logging import write_log
        write_log(
            "UPDATE",
            f"Admin changed role of {updated['firstname']} {updated['lastname']} to {new_role}",
            "user",
        )
        return jsonify({"message": "Role updated"}), 200
    except Exception as exc:
        if conn:
            conn.rollback()
        return jsonify({"error": str(exc)}), 500
    finally:
        if conn:
            conn.close()


# ── All cases overview ───────────────────────────────────────────────────────

@users_bp.route("/api/admin/cases", methods=["GET"])
@login_required
def admin_list_cases():
    err = _require_admin()
    if err:
        return err
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT
                c.caseid, c.title, c.casenumber, c.casetype,
                c.status, c.filingdate,
                (SELECT ct.courtname FROM courtaccess ca JOIN court ct ON ct.courtid = ca.courtid
                 WHERE ca.caseid = c.caseid LIMIT 1) AS courtname,
                (SELECT TRIM(u.firstname||' '||u.lastname) FROM judgeaccess ja
                 JOIN judge j ON j.judgeid = ja.judgeid JOIN users u ON u.userid = j.userid
                 WHERE ja.caseid = c.caseid LIMIT 1) AS judgename,
                (SELECT TRIM(u.firstname||' '||u.lastname) FROM caselawyeraccess cla
                 JOIN lawyer lw ON lw.lawyerid = cla.lawyerid JOIN users u ON u.userid = lw.userid
                 WHERE cla.caseid = c.caseid LIMIT 1) AS lawyername,
                (SELECT TRIM(u.firstname||' '||u.lastname) FROM caseparticipantaccess cpa
                 JOIN caseparticipant cp ON cp.participantid = cpa.participantid
                 JOIN users u ON u.userid = cp.userid
                 WHERE cpa.caseid = c.caseid LIMIT 1) AS clientname
            FROM cases c
            ORDER BY c.filingdate DESC NULLS LAST, c.caseid DESC
            """
        )
        rows = cur.fetchall()
        result = [{
            "caseid":     r["caseid"],
            "title":      r["title"],
            "casenumber": r["casenumber"] or "—",
            "casetype":   r["casetype"] or "—",
            "status":     r["status"],
            "filingdate": r["filingdate"].isoformat() if r["filingdate"] else None,
            "court":      r["courtname"] or "—",
            "judge":      r["judgename"] or "—",
            "lawyer":     r["lawyername"] or "—",
            "client":     r["clientname"] or "—",
        } for r in rows]
        return jsonify({"cases": result}), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if conn:
            conn.close()


# ── Activity feed (real data, no logtable dependency) ───────────────────────

@users_bp.route("/api/admin/activity", methods=["GET"])
@login_required
def admin_activity():
    err = _require_admin()
    if err:
        return err
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        events = []

        # Recent case registrations
        cur.execute(
            """
            SELECT c.caseid, c.title, c.casetype, c.filingdate, c.status,
                   TRIM(u.firstname||' '||u.lastname) AS clientname
            FROM cases c
            LEFT JOIN caseparticipantaccess cpa ON cpa.caseid = c.caseid
            LEFT JOIN caseparticipant cp ON cp.participantid = cpa.participantid
            LEFT JOIN users u ON u.userid = cp.userid
            ORDER BY c.filingdate DESC NULLS LAST, c.caseid DESC
            LIMIT 20
            """
        )
        for r in cur.fetchall():
            events.append({
                "type": "case_filed",
                "label": "Case Filed",
                "description": f"New {r['casetype'] or ''} case registered: {r['title']}",
                "date": r["filingdate"].isoformat() if r["filingdate"] else None,
                "entity": "case",
                "status": r["status"],
            })

        # Recent hearings
        cur.execute(
            """
            SELECT h.hearingdate, h.hearingstatus, c.title AS casetitle
            FROM hearings h
            JOIN cases c ON c.caseid = h.caseid
            ORDER BY h.hearingdate DESC NULLS LAST
            LIMIT 15
            """
        )
        for r in cur.fetchall():
            events.append({
                "type": "hearing",
                "label": "Hearing",
                "description": f"Hearing for '{r['casetitle']}' — {r['hearingstatus'] or 'scheduled'}",
                "date": r["hearingdate"].isoformat() if r["hearingdate"] else None,
                "entity": "hearing",
                "status": r["hearingstatus"] or "scheduled",
            })

        # Recent appeals
        cur.execute(
            """
            SELECT a.appealdate, a.appealstatus, a.decision, c.title AS casetitle
            FROM appeals a
            JOIN cases c ON c.caseid = a.caseid
            ORDER BY a.appealdate DESC NULLS LAST
            LIMIT 10
            """
        )
        for r in cur.fetchall():
            events.append({
                "type": "appeal",
                "label": "Appeal",
                "description": f"Appeal filed for '{r['casetitle']}'" + (f" — {r['decision']}" if r["decision"] else ""),
                "date": r["appealdate"].isoformat() if r["appealdate"] else None,
                "entity": "appeal",
                "status": r["appealstatus"] or "Pending",
            })

        # Recent final decisions
        cur.execute(
            """
            SELECT fd.decisiondate, fd.verdict, c.title AS casetitle
            FROM finaldecision fd
            JOIN cases c ON c.caseid = fd.caseid
            ORDER BY fd.decisiondate DESC NULLS LAST
            LIMIT 10
            """
        )
        for r in cur.fetchall():
            events.append({
                "type": "decision",
                "label": "Final Decision",
                "description": f"Case '{r['casetitle']}' closed — verdict: {r['verdict']}",
                "date": r["decisiondate"].isoformat() if r["decisiondate"] else None,
                "entity": "decision",
                "status": "Closed",
            })

        # Recent user registrations
        cur.execute(
            """
            SELECT userid, TRIM(firstname||' '||lastname) AS name, role, createdat
            FROM users
            ORDER BY createdat DESC NULLS LAST
            LIMIT 10
            """
        )
        for r in cur.fetchall():
            events.append({
                "type": "user_registered",
                "label": "User Registered",
                "description": f"New {r['role']} account: {r['name']}",
                "date": r["createdat"].isoformat() if r["createdat"] else None,
                "entity": "user",
                "status": "Success",
            })

        # Sort all events by date descending
        events.sort(key=lambda e: e["date"] or "0000-00-00", reverse=True)
        return jsonify({"activity": events[:60]}), 200

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if conn:
            conn.close()
