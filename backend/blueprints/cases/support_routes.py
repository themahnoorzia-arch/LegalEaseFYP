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
    db = SessionLocal()
    try:
        if current_user.role != "Lawyer":
            return jsonify({"message": "Access denied"}), 403

        lawyer = db.query(Lawyer).filter_by(userid=current_user.userid).first()
        if not lawyer:
            return jsonify({"bails": []}), 200

        bails = (
            db.query(Bail)
            .join(Cases, Bail.caseid == Cases.caseid)
            .join(Cases.lawyer)
            .filter(Lawyer.lawyerid == lawyer.lawyerid)
            .all()
        )

        result = [
            {
                "bailid": b.bailid,
                "caseid": b.caseid,
                "bailstatus": b.bailstatus,
                "bailamount": float(b.bailamount) if b.bailamount else None,
                "baildate": b.baildate.isoformat() if b.baildate else None,
                "remarks": b.remarks,
                "bailcondition": b.bailcondition,
            }
            for b in bails
        ]
        return jsonify({"bails": result}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        db.close()


@cases_bp.route("/surety/from-lawyer", methods=["GET"])
@login_required
def get_surety_by_lawyer():
    db = SessionLocal()
    try:
        if current_user.role != "Lawyer":
            return jsonify({"message": "Only lawyers can access this resource"}), 403

        lawyer = db.query(Lawyer).filter_by(userid=current_user.userid).first()
        if not lawyer:
            return jsonify({"message": "Lawyer not found"}), 404

        bail = (
            db.query(Bail)
            .join(Cases, Bail.caseid == Cases.caseid)
            .join(
                t_caselawyeraccess,
                t_caselawyeraccess.c.caseid == Cases.caseid,
            )
            .filter(t_caselawyeraccess.c.lawyerid == lawyer.lawyerid)
            .first()
        )

        if not bail:
            return jsonify({"message": "No bail found for this lawyer", "surety": None}), 200

        surety = bail.surety
        if not surety:
            return jsonify({"message": "Surety not found for the bail", "surety": None}), 200

        case = db.query(Cases).filter_by(caseid=bail.caseid).first()
        return jsonify(
            {
                "suretyid": surety.suretyid,
                "firstname": surety.firstname,
                "lastname": surety.lastname,
                "cnic": surety.cnic,
                "phone": surety.phone,
                "email": surety.email,
                "address": surety.address,
                "pasthistory": surety.pasthistory,
                "casename": case.title if case else "Unknown",
            }
        ), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        db.close()


@cases_bp.route("/lawyer/evidence", methods=["GET"])
@login_required
def get_evidence_for_logged_in_lawyer():
    db = SessionLocal()
    try:
        if current_user.role != "Lawyer":
            return jsonify({"message": "Access denied: User is not a lawyer"}), 403

        lawyer = db.query(Lawyer).filter_by(userid=current_user.userid).first()
        if not lawyer:
            return jsonify({"evidence": []}), 200

        case_ids = [
            row[0]
            for row in db.query(t_caselawyeraccess.c.caseid).filter(
                t_caselawyeraccess.c.lawyerid == lawyer.lawyerid
            ).all()
        ]

        if not case_ids:
            return jsonify({"evidence": []}), 200

        evidence_entries = (
            db.query(Evidence).filter(Evidence.caseid.in_(case_ids)).all()
        )
        result = [
            {
                "evidence_id": e.evidenceid,
                "case_id": e.caseid,
                "evidencetype": e.evidencetype,
                "description": e.description,
                "filepath": e.filepath,
                "submitteddate": (
                    e.submitteddate.isoformat() if e.submitteddate else None
                ),
            }
            for e in evidence_entries
        ]
        return jsonify({"evidence": result}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        db.close()


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
