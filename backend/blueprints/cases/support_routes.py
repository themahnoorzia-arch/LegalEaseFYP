"""Lawyer dashboard support routes migrated from the original monolithic app."""
import datetime

import psycopg2.extras
from flask import jsonify, request
from flask_login import login_required, current_user

from blueprints.cases import cases_bp
from db.db import SessionLocal, get_pg_connection
from models import (
    Bail,
    Cases,
    Evidence,
    Lawyer,
    Surety,
    Witnesscase,
    Witnesses,
    t_caselawyeraccess,
)


@cases_bp.route("/lawyerappeals", methods=["GET"])
@login_required
def get_lawyerappeals():
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT lawyerid FROM lawyer WHERE userid = %s;",
            (current_user.userid,),
        )
        lawyer_row = cur.fetchone()
        if not lawyer_row:
            return jsonify({"appeals": []}), 200

        cur.execute(
            """
            SELECT
                a.appealdate,
                a.appealstatus,
                a.decisiondate,
                a.decision,
                c.title AS casename,
                ct.courtname
            FROM appeals a
            JOIN cases c ON c.caseid = a.caseid
            JOIN courtaccess ca ON ca.caseid = c.caseid
            JOIN court ct ON ct.courtid = ca.courtid
            WHERE a.caseid IN (
                SELECT caseid FROM caselawyeraccess WHERE lawyerid = %s
            )
            """,
            (lawyer_row[0],),
        )
        rows = cur.fetchall()
        result = [
            {
                "appealdate": row[0],
                "status": row[1],
                "decisiondate": row[2],
                "decision": row[3],
                "casename": row[4],
                "courtname": row[5],
            }
            for row in rows
        ]
        return jsonify({"appeals": result}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        if conn:
            conn.close()


@cases_bp.route("/bails", methods=["GET"])
@login_required
def get_bails_for_lawyer():
    if current_user.role != "Lawyer":
        return jsonify({"message": "Access denied"}), 403
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT b.bailid, b.caseid, b.bailstatus, b.bailamount,
                   b.baildate, b.remarks, b.bailcondition
            FROM bail b
            JOIN caselawyeraccess cla ON cla.caseid = b.caseid
            JOIN lawyer l ON l.lawyerid = cla.lawyerid
            WHERE l.userid = %s
            """,
            (current_user.userid,),
        )
        rows = cur.fetchall()
        result = []
        for r in rows:
            row = dict(r)
            if row.get("baildate"):
                row["baildate"] = row["baildate"].isoformat()
            if row.get("bailamount"):
                row["bailamount"] = float(row["bailamount"])
            result.append(row)
        return jsonify({"bails": result}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        if conn:
            conn.close()


@cases_bp.route("/surety/from-lawyer", methods=["GET"])
@login_required
def get_surety_by_lawyer():
    if current_user.role != "Lawyer":
        return jsonify({"message": "Only lawyers can access this resource"}), 403
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT s.suretyid, s.firstname, s.lastname, s.cnic,
                   s.phone, s.email, s.address, s.pasthistory,
                   c.title AS casename
            FROM surety s
            JOIN bail b ON b.suretyid = s.suretyid
            JOIN caselawyeraccess cla ON cla.caseid = b.caseid
            JOIN lawyer l ON l.lawyerid = cla.lawyerid
            JOIN cases c ON c.caseid = b.caseid
            WHERE l.userid = %s
            LIMIT 1
            """,
            (current_user.userid,),
        )
        row = cur.fetchone()
        if not row:
            return jsonify({"message": "No surety found for this lawyer", "surety": None}), 200
        return jsonify(dict(row)), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        if conn:
            conn.close()


@cases_bp.route("/lawyer/evidence", methods=["GET"])
@login_required
def get_evidence_for_logged_in_lawyer():
    if current_user.role != "Lawyer":
        return jsonify({"message": "Access denied: User is not a lawyer"}), 403
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT e.evidenceid AS evidence_id, e.caseid AS case_id,
                   e.evidencetype, e.description, e.filepath, e.submitteddate
            FROM evidence e
            JOIN caselawyeraccess cla ON cla.caseid = e.caseid
            JOIN lawyer l ON l.lawyerid = cla.lawyerid
            WHERE l.userid = %s
            """,
            (current_user.userid,),
        )
        rows = cur.fetchall()
        result = []
        for r in rows:
            row = dict(r)
            if row.get("submitteddate"):
                row["submitteddate"] = row["submitteddate"].isoformat()
            result.append(row)
        return jsonify({"evidence": result}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        if conn:
            conn.close()


@cases_bp.route("/documents", methods=["GET"])
@login_required
def get_documents():
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT d.documenttitle, d.documenttype, d.uploaddate
            FROM documents d
            JOIN documentcase cd ON d.documentid = cd.documentid
            JOIN caselawyeraccess la ON cd.caseid = la.caseid
            JOIN lawyer l ON la.lawyerid = l.lawyerid
            WHERE l.userid = %s
            ORDER BY d.uploaddate DESC
            """,
            (current_user.userid,),
        )
        documents = cur.fetchall()
        for doc in documents:
            if isinstance(doc["uploaddate"], datetime.datetime):
                doc["uploaddate"] = doc["uploaddate"].isoformat()
        return jsonify({"documents": documents})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@cases_bp.route("/witnesses", methods=["GET"])
@login_required
def get_all_witnesses():
    db = SessionLocal()
    try:
        witnesses = db.query(Witnesses).all()
        if not witnesses:
            return jsonify({"witnesses": []}), 200

        result = []
        for witness in witnesses:
            witness_cases = (
                db.query(Witnesscase)
                .filter_by(witnessid=witness.witnessid)
                .all()
            )
            cases = []
            for link in witness_cases:
                case = db.query(Cases).filter_by(caseid=link.caseid).first()
                if case:
                    cases.append(
                        {
                            "caseid": case.caseid,
                            "title": case.title,
                            "statement": link.statement,
                        }
                    )
            result.append(
                {
                    "witness": {
                        "id": witness.witnessid,
                        "firstname": witness.firstname,
                        "lastname": witness.lastname,
                        "cnic": witness.cnic,
                        "phone": witness.phone,
                        "email": witness.email,
                        "address": witness.address,
                        "pasthistory": witness.pasthistory,
                    },
                    "cases": cases,
                }
            )
        return jsonify({"witnesses": result}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        db.close()


@cases_bp.route("/evidence", methods=["GET"])
@login_required
def get_all_evidence():
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT
                e.evidenceid    AS id,
                e.evidencetype  AS "evidenceType",
                e.description,
                e.filepath,
                e.submitteddate AS date,
                c.title         AS "caseName"
            FROM evidence e
            JOIN cases c ON c.caseid = e.caseid
            ORDER BY e.submitteddate DESC NULLS LAST
            """
        )
        rows = cur.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "evidenceType": row["evidenceType"],
                "description": row["description"],
                "filepath": row["filepath"],
                "date": row["date"].isoformat() if row["date"] else None,
                "caseName": row["caseName"],
            })
        return jsonify({"evidence": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
