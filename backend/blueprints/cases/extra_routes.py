"""Routes migrated from the legacy monolithic app (documents, hearings write, decisions)."""
import datetime

from flask import jsonify, request
from flask_login import login_required, current_user

import psycopg2.extras

from blueprints.cases import cases_bp
from db.db import SessionLocal, get_pg_connection
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


@cases_bp.route("/cases/<int:case_id>/documents", methods=["GET"])
@login_required
def get_case_documents(case_id):
    db = SessionLocal()
    try:
        links = db.query(Documentcase).filter_by(caseid=case_id).all()
        result = []
        for link in links:
            doc = db.query(Documents).filter_by(documentid=link.documentid).first()
            if doc:
                result.append({
                    "id": doc.documentid,
                    "title": doc.documenttitle,
                    "path": doc.filepath,
                    "uploadDate": (
                        doc.uploaddate.isoformat() if doc.uploaddate else ""
                    ),
                    "type": doc.documenttype or "Document",
                    "submissiondate": (
                        link.submissiondate.isoformat()
                        if link.submissiondate
                        else ""
                    ),
                })
        return jsonify({"documents": result}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        db.close()


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


@cases_bp.route("/documents", methods=["POST"])
@login_required
def upload_document():
    data = request.get_json() or {}
    required = ["documenttitle", "documenttype", "uploaddate"]
    if not all(field in data for field in required):
        return jsonify({"error": "Missing required fields"}), 400

    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        upload_date = data["uploaddate"]
        if "T" in str(upload_date):
            upload_date = str(upload_date).split("T")[0]

        cur.execute(
            """
            INSERT INTO documents (documenttitle, documenttype, uploaddate, filepath)
            VALUES (%s, %s, %s, %s)
            RETURNING documentid
            """,
            (
                data["documenttitle"],
                data["documenttype"],
                upload_date,
                data.get("filepath", "/uploads/placeholder.pdf"),
            ),
        )
        new_id = cur.fetchone()[0]

        case_id = data.get("caseid")
        if case_id:
            cur.execute(
                """
                INSERT INTO documentcase (caseid, documentid, submissiondate)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (case_id, new_id, datetime.date.today()),
            )

        conn.commit()
        return jsonify({
            "message": "Document uploaded successfully",
            "document_id": new_id,
        }), 201
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
