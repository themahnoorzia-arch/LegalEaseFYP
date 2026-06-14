import datetime
from decimal import Decimal

import psycopg2.extras

from flask import jsonify, request
from flask_login import login_required, current_user

from blueprints.financials import financials_bp
from db.db import get_pg_connection


# ==========================================================
# GET PAYMENTS
# ==========================================================
@financials_bp.route("/api/payments", methods=["GET"])
@login_required
def get_payments():
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        if current_user.role == "Lawyer":
            cur.execute(
                """
                SELECT p.paymentid, p.paymentdate, p.purpose, p.balance,
                       p.mode, p.paymenttype, p.status,
                       c.title AS casename, ct.courtname,
                       TRIM(lu.firstname || ' ' || lu.lastname) AS lawyer_name
                FROM payments p
                JOIN lawyer l ON l.lawyerid = p.lawyerid
                JOIN users lu ON lu.userid = l.userid
                JOIN cases c ON c.caseid = p.caseid
                LEFT JOIN court ct ON ct.courtid = p.courtid
                WHERE l.userid = %s
                ORDER BY p.paymentdate DESC NULLS LAST
                """,
                (current_user.userid,),
            )

        elif current_user.role == "CourtRegistrar":
            cur.execute(
                """
                SELECT p.paymentid, p.paymentdate, p.purpose, p.balance,
                       p.mode, p.paymenttype, p.status,
                       c.title AS casename, ct.courtname,
                       TRIM(lu.firstname || ' ' || lu.lastname) AS lawyer_name
                FROM payments p
                JOIN cases c ON c.caseid = p.caseid
                JOIN court ct ON ct.courtid = p.courtid
                JOIN courtregistrar cr ON cr.courtid = ct.courtid
                LEFT JOIN lawyer l ON l.lawyerid = p.lawyerid
                LEFT JOIN users lu ON lu.userid = l.userid
                WHERE cr.userid = %s
                ORDER BY p.paymentdate DESC NULLS LAST
                """,
                (current_user.userid,),
            )

        else:
            return jsonify({"status": "error", "message": "Unauthorized role"}), 403

        rows = cur.fetchall()
        result = []
        for r in rows:
            row = dict(r)
            if row.get("paymentdate"):
                row["paymentdate"] = row["paymentdate"].isoformat()
            if row.get("balance") is not None:
                row["balance"] = float(row["balance"])
            result.append(row)

        return jsonify({"status": "success", "payments": result}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if conn:
            conn.close()


# ==========================================================
# CREATE PAYMENT REQUEST (Registrar only)
# ==========================================================
@financials_bp.route("/api/payments", methods=["POST"])
@login_required
def create_payment():
    if current_user.role != "CourtRegistrar":
        return jsonify({"message": "Only court registrars can create payment requests"}), 403

    data = request.get_json() or {}
    case_id = data.get("caseid")
    purpose = data.get("purpose", "").strip()
    balance = data.get("balance")
    payment_type = data.get("paymenttype", "Court Fee").strip()

    if not case_id or not purpose or balance is None:
        return jsonify({"message": "caseid, purpose, and balance are required"}), 400

    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Get registrar's court
        cur.execute(
            "SELECT courtid FROM courtregistrar WHERE userid = %s",
            (current_user.userid,),
        )
        reg = cur.fetchone()
        if not reg:
            return jsonify({"message": "Registrar profile not found"}), 404
        court_id = reg["courtid"]

        # Get the lawyer on this case
        cur.execute(
            """
            SELECT l.lawyerid FROM caselawyeraccess cla
            JOIN lawyer l ON l.lawyerid = cla.lawyerid
            WHERE cla.caseid = %s
            LIMIT 1
            """,
            (case_id,),
        )
        lawyer_row = cur.fetchone()
        lawyer_id = lawyer_row["lawyerid"] if lawyer_row else None

        cur.execute(
            """
            INSERT INTO payments (purpose, balance, paymenttype, caseid, courtid, lawyerid, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
            RETURNING paymentid
            """,
            (purpose, Decimal(str(balance)), payment_type, case_id, court_id, lawyer_id),
        )
        new_id = cur.fetchone()["paymentid"]
        conn.commit()

        # Notify the lawyer
        try:
            from utils.notifications import push_notification
            if lawyer_id:
                cur.execute("SELECT userid FROM lawyer WHERE lawyerid = %s", (lawyer_id,))
                lr = cur.fetchone()
                if lr:
                    push_notification(lr["userid"], "New Payment Request",
                        f"A payment request of PKR {balance} has been sent to you for a case. Please confirm payment.",
                        "warning", new_id)
        except Exception:
            pass

        return jsonify({"message": "Payment request created", "paymentid": new_id}), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"message": str(e)}), 500
    finally:
        if conn:
            conn.close()


# ==========================================================
# CONFIRM PAYMENT (Lawyer only)
# ==========================================================
@financials_bp.route("/api/payments/<int:payment_id>/confirm", methods=["PATCH"])
@login_required
def confirm_payment(payment_id):
    if current_user.role != "Lawyer":
        return jsonify({"message": "Only lawyers can confirm payments"}), 403

    data = request.get_json() or {}
    mode = data.get("mode", "").strip()
    payment_date = data.get("paymentdate") or datetime.date.today().isoformat()

    valid_modes = ["Cash", "Credit/Debit card", "Online Transfer"]
    if mode not in valid_modes:
        return jsonify({"message": f"Mode must be one of: {', '.join(valid_modes)}"}), 400

    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Verify the payment belongs to this lawyer
        cur.execute(
            """
            SELECT p.paymentid FROM payments p
            JOIN lawyer l ON l.lawyerid = p.lawyerid
            WHERE p.paymentid = %s AND l.userid = %s AND p.status = 'Pending'
            """,
            (payment_id, current_user.userid),
        )
        if not cur.fetchone():
            return jsonify({"message": "Payment not found or already confirmed"}), 404

        cur.execute(
            """
            UPDATE payments
            SET mode = %s, paymentdate = %s, status = 'Paid'
            WHERE paymentid = %s
            """,
            (mode, payment_date, payment_id),
        )
        conn.commit()

        # Notify the registrar who created this payment
        try:
            from utils.notifications import push_notification
            cur.execute(
                """SELECT cr.userid FROM courtregistrar cr
                   JOIN payments p ON p.courtid = cr.courtid
                   WHERE p.paymentid = %s""",
                (payment_id,),
            )
            reg = cur.fetchone()
            if reg:
                push_notification(reg["userid"], "Payment Confirmed",
                    f"A lawyer has confirmed payment #{payment_id}.", "success", payment_id)
        except Exception:
            pass

        return jsonify({"message": "Payment confirmed"}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"message": str(e)}), 500
    finally:
        if conn:
            conn.close()
