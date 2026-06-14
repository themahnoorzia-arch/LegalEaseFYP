"""Routes migrated from the legacy monolithic app (documents, hearings write, decisions)."""
import datetime
import os
import uuid

from flask import jsonify, request, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

import psycopg2.extras

from blueprints.cases import cases_bp
from db.db import SessionLocal, get_pg_connection

# ---------------------------------------------------------------------------
# File storage helpers
# ---------------------------------------------------------------------------
_UPLOAD_BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', 'uploads')
)
_ALLOWED = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt', 'xlsx', 'xls'}


def _case_folder(case_id):
    folder = os.path.join(_UPLOAD_BASE, f'case_{case_id}')
    os.makedirs(folder, exist_ok=True)
    return folder


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in _ALLOWED


# ---------------------------------------------------------------------------
# Access control helpers
# ---------------------------------------------------------------------------
def _user_has_case_access(cur, userid, role, case_id):
    """Return True if the user has any association with this case."""
    if role in ('CourtRegistrar', 'Admin'):
        cur.execute("SELECT 1 FROM cases WHERE caseid = %s", (case_id,))
        return bool(cur.fetchone())
    if role == 'Lawyer':
        cur.execute(
            """SELECT 1 FROM caselawyeraccess cla
               JOIN lawyer l ON l.lawyerid = cla.lawyerid
               WHERE cla.caseid = %s AND l.userid = %s""",
            (case_id, userid),
        )
    elif role == 'Judge':
        cur.execute(
            """SELECT 1 FROM judgeaccess ja
               JOIN judge j ON j.judgeid = ja.judgeid
               WHERE ja.caseid = %s AND j.userid = %s""",
            (case_id, userid),
        )
    elif role in ('Client', 'CaseParticipant'):
        cur.execute(
            """SELECT 1 FROM caseparticipantaccess cpa
               JOIN caseparticipant cp ON cp.participantid = cpa.participantid
               WHERE cpa.caseid = %s AND cp.userid = %s""",
            (case_id, userid),
        )
    else:
        return False
    return bool(cur.fetchone())


def _visibility_sql(role):
    """Return SQL fragment for which visibility levels the role can see (excluding own docs)."""
    if role == 'Judge':
        return "d.visibility = 'court'"
    if role in ('CourtRegistrar', 'Admin'):
        # Registrar sees court + team (they manage cases)
        return "d.visibility IN ('court', 'team')"
    # Lawyer, Client, CaseParticipant — see court + team
    return "d.visibility IN ('court', 'team')"
from models import (
    Cases,
    Casehistory,
    Documents,
    Documentcase,
    Finaldecision,
    Judge,
    Lawyer,
    Users,
)


@cases_bp.route("/cases/history", methods=["GET"])
@login_required
def get_all_case_history():
    """
    Return all case history entries enriched with case metadata.
    Used by the Manage Case History page in the registrar dashboard.
    Each row includes case name, case number, judge, client, lawyer, status.
    """
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(
            """
            SELECT
                ch.historyid,
                ch.actiondate,
                ch.actiontaken,
                ch.remarks,
                c.caseid,
                c.title      AS casename,
                c.casenumber,
                c.status,
                (
                    SELECT TRIM(u.firstname || ' ' || u.lastname)
                    FROM judgeaccess ja
                    JOIN judge j ON j.judgeid = ja.judgeid
                    JOIN users u ON u.userid  = j.userid
                    WHERE ja.caseid = c.caseid LIMIT 1
                ) AS judgename,
                (
                    SELECT TRIM(u.firstname || ' ' || u.lastname)
                    FROM caseparticipantaccess cpa
                    JOIN caseparticipant cp ON cp.participantid = cpa.participantid
                    JOIN users u            ON u.userid         = cp.userid
                    WHERE cpa.caseid = c.caseid LIMIT 1
                ) AS clientname,
                (
                    SELECT TRIM(u.firstname || ' ' || u.lastname)
                    FROM caselawyeraccess cla
                    JOIN lawyer lw ON lw.lawyerid = cla.lawyerid
                    JOIN users u   ON u.userid    = lw.userid
                    WHERE cla.caseid = c.caseid LIMIT 1
                ) AS lawyername
            FROM casehistory ch
            JOIN cases c ON c.caseid = ch.caseid
            ORDER BY ch.actiondate DESC NULLS LAST, ch.historyid DESC
            """
        )

        rows = cur.fetchall()
        result = [
            {
                "historyid":   r["historyid"],
                "caseid":      r["caseid"],
                "caseName":    r["casename"],
                "casenumber":  r["casenumber"] or "—",
                "judgeName":   r["judgename"]  or "—",
                "clientName":  r["clientname"] or "—",
                "lawyerName":  r["lawyername"] or "—",
                "actionDate":  r["actiondate"].isoformat() if r["actiondate"] else None,
                "actionTaken": r["actiontaken"],
                "remarks":     r["remarks"] or "",
                "status":      r["status"],
                "eventType":   "manual",
            }
            for r in rows
        ]

        return jsonify({"history": result}), 200

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if conn:
            conn.close()


@cases_bp.route("/cases/<int:case_id>/documents", methods=["GET"])
@login_required
def get_case_documents(case_id):
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        role = current_user.role
        userid = current_user.userid

        if not _user_has_case_access(cur, userid, role, case_id):
            return jsonify({"error": "Access denied"}), 403

        vis_sql = _visibility_sql(role)
        cur.execute(
            f"""
            SELECT d.documentid AS id,
                   d.documenttitle AS title,
                   d.documenttype AS type,
                   d.uploaddate,
                   d.filepath,
                   d.visibility,
                   d.uploaded_by,
                   TRIM(u.firstname || ' ' || u.lastname) AS uploader_name
            FROM documents d
            JOIN documentcase dc ON dc.documentid = d.documentid
            LEFT JOIN users u ON u.userid = d.uploaded_by
            WHERE dc.caseid = %s
              AND (d.uploaded_by = %s OR {vis_sql})
            ORDER BY d.uploaddate DESC
            """,
            (case_id, userid),
        )
        docs = [dict(r) for r in cur.fetchall()]
        # mark which docs the current user owns (for delete permission on frontend)
        for d in docs:
            d['is_own'] = (d['uploaded_by'] == userid)
            if d['uploaddate']:
                d['uploaddate'] = d['uploaddate'].isoformat()
        return jsonify({"documents": docs}), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if conn:
            conn.close()


@cases_bp.route("/cases/<int:case_id>/documents", methods=["POST"])
@login_required
def upload_case_document(case_id):
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        role = current_user.role
        userid = current_user.userid

        if not _user_has_case_access(cur, userid, role, case_id):
            return jsonify({"error": "Access denied"}), 403

        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        if not _allowed_file(file.filename):
            return jsonify({"error": "File type not allowed"}), 400

        doc_type = request.form.get('documenttype', 'Other')
        visibility = request.form.get('visibility', 'court')
        if visibility not in ('court', 'team', 'private'):
            visibility = 'court'

        # Judges cannot upload 'team' docs (they're not part of lawyer-client team)
        if role == 'Judge' and visibility == 'team':
            visibility = 'court'

        # Save file
        ext = file.filename.rsplit('.', 1)[1].lower()
        stored_name = f"{uuid.uuid4().hex}.{ext}"
        folder = _case_folder(case_id)
        file.save(os.path.join(folder, stored_name))
        relative_path = f'/uploads/case_{case_id}/{stored_name}'

        cur.execute(
            """
            INSERT INTO documents
                (documenttitle, documenttype, uploaddate, filepath, uploaded_by, visibility)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING documentid
            """,
            (
                secure_filename(file.filename),
                doc_type,
                datetime.date.today(),
                relative_path,
                userid,
                visibility,
            ),
        )
        doc_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO documentcase (caseid, documentid, submissiondate)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (case_id, doc_id, datetime.date.today()),
        )
        conn.commit()
        return jsonify({"message": "Document uploaded", "document_id": doc_id}), 201

    except Exception as exc:
        if conn:
            conn.rollback()
        return jsonify({"error": str(exc)}), 500
    finally:
        if conn:
            conn.close()


@cases_bp.route("/cases/<int:case_id>/documents/<int:doc_id>", methods=["DELETE"])
@login_required
def delete_case_document(case_id, doc_id):
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(
            "SELECT * FROM documents WHERE documentid = %s AND uploaded_by = %s",
            (doc_id, current_user.userid),
        )
        doc = cur.fetchone()
        if not doc:
            return jsonify({"error": "Not found or not authorized"}), 403

        # Remove file from disk
        filepath = doc['filepath']
        abs_path = os.path.join(_UPLOAD_BASE, *filepath.lstrip('/').split('/')[1:])
        if os.path.exists(abs_path):
            os.remove(abs_path)

        cur.execute("DELETE FROM documentcase WHERE documentid = %s", (doc_id,))
        cur.execute("DELETE FROM documents WHERE documentid = %s", (doc_id,))
        conn.commit()
        return jsonify({"message": "Deleted"}), 200

    except Exception as exc:
        if conn:
            conn.rollback()
        return jsonify({"error": str(exc)}), 500
    finally:
        if conn:
            conn.close()


@cases_bp.route("/documents/<int:doc_id>/download", methods=["GET"])
@login_required
def download_document(doc_id):
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(
            """SELECT d.*, dc.caseid FROM documents d
               JOIN documentcase dc ON dc.documentid = d.documentid
               WHERE d.documentid = %s""",
            (doc_id,),
        )
        doc = cur.fetchone()
        if not doc:
            return jsonify({"error": "Not found"}), 404

        case_id = doc['caseid']
        role = current_user.role
        userid = current_user.userid

        # Must have case access
        if not _user_has_case_access(cur, userid, role, case_id):
            return jsonify({"error": "Access denied"}), 403

        # Check visibility
        vis = doc['visibility']
        if vis == 'private' and doc['uploaded_by'] != userid:
            return jsonify({"error": "Access denied"}), 403
        if vis == 'team' and role == 'Judge':
            return jsonify({"error": "Access denied"}), 403

        # Serve file
        filepath = doc['filepath']  # e.g. /uploads/case_1/abc.pdf
        parts = filepath.lstrip('/').split('/', 1)  # ['uploads', 'case_1/abc.pdf']
        abs_path = os.path.join(_UPLOAD_BASE, parts[1]) if len(parts) > 1 else None

        if not abs_path or not os.path.exists(abs_path):
            return jsonify({"error": "File not found on server"}), 404

        return send_file(
            abs_path,
            as_attachment=True,
            download_name=doc['documenttitle'],
        )

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if conn:
            conn.close()


@cases_bp.route("/cases/<int:case_id>/final-decision", methods=["POST"])
@login_required
def add_final_decision(case_id):
    conn = None
    try:
        data = request.get_json() or {}
        decision_summary = data.get("decisionsummary")
        verdict = data.get("verdict")
        decision_date = data.get("decisiondate") or datetime.date.today().isoformat()

        if not decision_summary or not verdict:
            return jsonify({
                "message": "Decision summary and verdict are required",
            }), 400

        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM cases WHERE caseid = %s", (case_id,))
        if not cur.fetchone():
            return jsonify({"message": "Case not found"}), 404

        cur.execute(
            """
            INSERT INTO finaldecision (caseid, decisionsummary, verdict, decisiondate)
            VALUES (%s, %s, %s, %s)
            RETURNING decisionid
            """,
            (case_id, decision_summary, verdict, decision_date),
        )
        decision_id = cur.fetchone()[0]

        cur.execute(
            "UPDATE cases SET status = 'Closed' WHERE caseid = %s",
            (case_id,),
        )
        cur.execute(
            """
            INSERT INTO casehistory (caseid, actiondate, actiontaken, remarks)
            VALUES (%s, %s, %s, %s)
            """,
            (
                case_id,
                decision_date,
                f"Case closed with verdict: {verdict}",
                decision_summary,
            ),
        )
        conn.commit()

        # Notify lawyers and clients
        try:
            from utils.notifications import push_notification
            nc = conn.cursor()
            nc.execute(
                "SELECT l.userid FROM lawyer l JOIN caselawyeraccess cla ON cla.lawyerid = l.lawyerid WHERE cla.caseid = %s",
                (case_id,),
            )
            for row in nc.fetchall():
                push_notification(row[0], "Case Decision Recorded",
                    f"A final verdict '{verdict}' has been recorded for case #{case_id}.", "success", case_id)
            nc.execute(
                "SELECT cp.userid FROM caseparticipant cp JOIN caseparticipantaccess cpa ON cpa.participantid = cp.participantid WHERE cpa.caseid = %s",
                (case_id,),
            )
            for row in nc.fetchall():
                push_notification(row[0], "Case Decision Recorded",
                    f"A final verdict has been recorded for your case. Verdict: {verdict}.", "success", case_id)
        except Exception:
            pass

        return jsonify({
            "message": "Final decision added successfully",
            "decision_id": decision_id,
        }), 201
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"message": str(e)}), 500
    finally:
        if conn:
            conn.close()


