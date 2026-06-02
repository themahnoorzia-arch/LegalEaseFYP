import datetime
from decimal import Decimal

import psycopg2
import psycopg2.extras

from flask import jsonify, request
from flask_login import login_required, current_user

from blueprints.financials import financials_bp
from db.db import SessionLocal, get_pg_connection

from models import (
    Payments,
    Cases,
    Lawyer,
    Court,
    Courtregistrar,
    t_courtaccess,
)


# ==========================================================
# GET PAYMENTS
# ==========================================================
@financials_bp.route("/api/payments", methods=["GET"])
@login_required
def get_payments():

    db = SessionLocal()

    try:

        # --------------------------------------------------
        # LAWYER VIEW
        # --------------------------------------------------
        if current_user.role == "Lawyer":

            lawyer = (
                db.query(Lawyer)
                .filter_by(userid=current_user.userid)
                .first()
            )

            if not lawyer:
                return jsonify({
                    "status": "error",
                    "message": "Lawyer profile not found"
                }), 404

            payments = (
                db.query(Payments)
                .filter_by(lawyerid=lawyer.lawyerid)
                .join(Cases, Payments.caseid == Cases.caseid)
                .join(
                    t_courtaccess,
                    Payments.caseid == t_courtaccess.c.caseid
                )
                .join(
                    Court,
                    t_courtaccess.c.courtid == Court.courtid
                )
                .with_entities(
                    Payments.paymentdate,
                    Cases.title.label("casename"),
                    Payments.purpose,
                    Payments.balance,
                    Payments.mode,
                    Payments.paymenttype,
                    Payments.status,
                    Court.courtname,
                )
                .all()
            )

        # --------------------------------------------------
        # REGISTRAR VIEW
        # --------------------------------------------------
        elif current_user.role == "CourtRegistrar":

            registrar = (
                db.query(Courtregistrar)
                .filter_by(userid=current_user.userid)
                .first()
            )

            if not registrar:
                return jsonify({
                    "status": "error",
                    "message": "Court registrar profile not found"
                }), 404

            payments = (
                db.query(Payments)
                .join(
                    Cases,
                    Payments.caseid == Cases.caseid
                )
                .join(
                    t_courtaccess,
                    t_courtaccess.c.caseid == Cases.caseid
                )
                .filter(
                    t_courtaccess.c.courtid == registrar.courtid
                )
                .join(
                    Court,
                    t_courtaccess.c.courtid == Court.courtid
                )
                .with_entities(
                    Payments.paymentdate,
                    Cases.title.label("casename"),
                    Payments.purpose,
                    Payments.balance,
                    Payments.mode,
                    Payments.paymenttype,
                    Payments.status,
                    Court.courtname,
                )
                .all()
            )

        else:

            return jsonify({
                "status": "error",
                "message": "Unauthorized role"
            }), 403

        result = []

        for p in payments:

            result.append({
                "paymentdate": str(p.paymentdate),
                "casename": p.casename,
                "purpose": p.purpose,
                "balance": float(p.balance),
                "mode": p.mode,
                "paymenttype": p.paymenttype,
                "status": p.status,
                "courtname": p.courtname,
            })

        return jsonify({
            "status": "success",
            "payments": result
        }), 200

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

    finally:
        db.close()


# ==========================================================
# CREATE PAYMENT
# ==========================================================
@financials_bp.route("/api/payments", methods=["POST"])
@login_required
def create_payment():

    data = request.get_json()

    casename = data.get("casename")
    purpose = data.get("purpose")
    balance = data.get("balance")
    mode = data.get("mode")
    paymenttype = data.get("paymenttype")

    paymentdate = (
        data.get("paymentdate")
        or datetime.date.today()
    )

    if not all([
        casename,
        purpose,
        balance,
        mode,
        paymenttype
    ]):
        return jsonify({
            "message": "Missing required fields"
        }), 400

    conn = None

    try:

        conn = get_pg_connection()

        cur = conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        )

        # --------------------------------------------
        # LAWYER ID
        # --------------------------------------------
        cur.execute(
            """
            SELECT lawyerid
            FROM lawyer
            WHERE userid = %s
            """,
            (current_user.userid,)
        )

        lawyer_row = cur.fetchone()

        if not lawyer_row:
            return jsonify({
                "message": "Lawyer not found"
            }), 404

        lawyerid = lawyer_row["lawyerid"]

        # --------------------------------------------
        # CASE ID
        # --------------------------------------------
        cur.execute(
            """
            SELECT caseid
            FROM cases
            WHERE title = %s
            """,
            (casename,)
        )

        case_row = cur.fetchone()

        if not case_row:
            return jsonify({
                "message": "Case not found"
            }), 404

        caseid = case_row["caseid"]

        # --------------------------------------------
        # COURT ID
        # --------------------------------------------
        cur.execute(
            """
            SELECT courtid
            FROM courtaccess
            WHERE caseid = %s
            """,
            (caseid,)
        )

        court_row = cur.fetchone()

        if not court_row:
            return jsonify({
                "message": "Court access not found"
            }), 404

        courtid = court_row["courtid"]

        # --------------------------------------------
        # INSERT PAYMENT
        # --------------------------------------------
        cur.execute(
            """
            INSERT INTO payments
            (
                mode,
                purpose,
                balance,
                paymentdate,
                lawyerid,
                caseid,
                courtid,
                paymenttype
            )
            VALUES
            (
                %s,%s,%s,%s,%s,%s,%s,%s
            )
            """,
            (
                mode,
                purpose,
                Decimal(balance),
                paymentdate,
                lawyerid,
                caseid,
                courtid,
                paymenttype,
            )
        )

        conn.commit()

        return jsonify({
            "message": "Payment recorded successfully",
            "payment": {
                "paymentdate": str(paymentdate),
                "casename": casename,
                "purpose": purpose,
                "balance": float(balance),
                "mode": mode,
                "paymenttype": paymenttype,
            }
        }), 201

    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify({
            "message": str(e)
        }), 500

    finally:

        if conn:
            conn.close()