from flask import jsonify, request
from flask_login import login_required, current_user

import psycopg2
import psycopg2.extras

from blueprints.court import court_bp
from db.db import SessionLocal, get_pg_connection

from models import (
    Court,
    Courtregistrar,
)


# ==========================================================
# CREATE COURT
# ==========================================================
@court_bp.route("/api/court", methods=["POST"])
@login_required
def add_court():
    db = SessionLocal()

    try:
        data = request.get_json()

        courtname = data.get("name")
        court_type = data.get("courtType")
        location = data.get("address")

        if not courtname or not court_type or not location:
            return jsonify({
                "status": "error",
                "message": "All fields are required"
            }), 400

        new_court = Court(
            courtname=courtname,
            type=court_type,
            location=location
        )

        db.add(new_court)
        db.flush()

        if current_user.role == "CourtRegistrar":

            registrar = (
                db.query(Courtregistrar)
                .filter_by(userid=current_user.userid)
                .first()
            )

            if not registrar:
                return jsonify({
                    "status": "error",
                    "message": "CourtRegistrar profile not found"
                }), 404

            registrar.courtid = new_court.courtid

        db.commit()

        return jsonify({
            "status": "success",
            "message": "Court added successfully",
            "court_id": new_court.courtid
        }), 201

    except Exception as e:
        db.rollback()

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

    finally:
        db.close()


# ==========================================================
# GET COURT
# ==========================================================
@court_bp.route("/api/court", methods=["GET"])
@login_required
def get_court_for_registrar():
    db = SessionLocal()

    try:
        registrar = (
            db.query(Courtregistrar)
            .filter_by(userid=current_user.userid)
            .first()
        )

        if not registrar:
            return jsonify(
                success=False,
                message="Registrar profile not found"
            ), 404

        if not registrar.courtid:
            return jsonify(
                success=False,
                message="Registrar is not assigned to any court"
            ), 404

        court = db.query(Court).get(registrar.courtid)

        if not court:
            return jsonify(
                success=False,
                message="Court not found"
            ), 404

        return jsonify(
            success=True,
            data={
                "id": court.courtid,
                "courtname": court.courtname,
                "type": court.type,
                "location": court.location
            }
        ), 200

    except Exception as e:
        return jsonify(
            success=False,
            message=str(e)
        ), 500

    finally:
        db.close()


@court_bp.route("/api/courts", methods=["GET"])
@login_required
def list_courts():
    """Return a list of all courts (id and courtname) for dropdowns."""
    db = SessionLocal()
    try:
        courts = db.query(Court).all()
        data = [{
            "id": c.courtid,
            "courtname": c.courtname,
        } for c in courts]
        return jsonify({"success": True, "courts": data}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        db.close()


# ==========================================================
# CREATE COURTROOM
# ==========================================================
@court_bp.route("/api/courtrooms", methods=["POST"])
@login_required
def create_courtroom():
    data = request.get_json()

    number = data.get("number")
    capacity = data.get("capacity")
    availability = data.get("availability")

    if not number or not capacity:
        return jsonify({
            "message": "Missing required fields"
        }), 400

    conn = None

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT courtid
            FROM courtregistrar
            WHERE userid = %s
        """, (current_user.userid,))

        row = cur.fetchone()

        if not row:
            return jsonify({
                "message": "Court registrar not found"
            }), 404

        courtid = row[0]

        cur.execute("""
            INSERT INTO courtroom
            (
                courtroomno,
                capacity,
                availability,
                courtid
            )
            VALUES (%s,%s,%s,%s)
        """, (
            number,
            capacity,
            availability,
            courtid
        ))

        conn.commit()

        return jsonify({
            "message": "Courtroom created successfully"
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


# ==========================================================
# UPDATE COURTROOM
# ==========================================================
@court_bp.route("/api/courtrooms/<int:courtroom_id>", methods=["PUT"])
@login_required
def update_courtroom(courtroom_id):

    data = request.get_json()

    number = data.get("number")
    capacity = data.get("capacity")
    availability = data.get("status")

    conn = None

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT 1
            FROM courtroom
            WHERE courtroomid=%s
            """,
            (courtroom_id,)
        )

        if not cur.fetchone():
            return jsonify({
                "message": "Courtroom not found"
            }), 404

        cur.execute("""
            UPDATE courtroom
            SET
                courtroomno=%s,
                capacity=%s,
                availability=%s
            WHERE courtroomid=%s
        """, (
            number,
            capacity,
            availability,
            courtroom_id
        ))

        conn.commit()

        return jsonify({
            "message": "Courtroom updated successfully"
        })

    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify({
            "message": str(e)
        }), 500

    finally:
        if conn:
            conn.close()


# ==========================================================
# DELETE COURTROOM
# ==========================================================
@court_bp.route("/api/courtrooms/<int:courtroom_id>", methods=["DELETE"])
@login_required
def delete_courtroom(courtroom_id):

    conn = None

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 1
            FROM courtroom
            WHERE courtroomid=%s
        """, (courtroom_id,))

        if not cur.fetchone():
            return jsonify({
                "message": "Courtroom not found"
            }), 404

        cur.execute("""
            DELETE FROM courtroom
            WHERE courtroomid=%s
        """, (courtroom_id,))

        conn.commit()

        return jsonify({
            "message": "Courtroom deleted successfully"
        })

    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify({
            "message": str(e)
        }), 500

    finally:
        if conn:
            conn.close()


# ==========================================================
# GET ALL COURTROOMS
# ==========================================================
@court_bp.route("/api/courtrooms", methods=["GET"])
@login_required
def get_courtrooms():

    conn = None

    try:
        conn = get_pg_connection()

        cur = conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        )

        cur.execute("""
            SELECT
                courtroomno,
                capacity,
                availability
            FROM courtroom
        """)

        rows = cur.fetchall()

        result = []

        for row in rows:
            result.append({
                "number": row["courtroomno"],
                "capacity": row["capacity"],
                "status": row["availability"]
            })

        return jsonify({
            "courtrooms": result
        }), 200

    except Exception as e:

        return jsonify({
            "message": str(e)
        }), 500

    finally:
        if conn:
            conn.close()


# ==========================================================
# GET COURTROOMS BY COURT
# ==========================================================
@court_bp.route("/api/courtrooms/<int:courtid>", methods=["GET"])
@login_required
def get_courtrooms_by_court(courtid):

    conn = None

    try:
        conn = get_pg_connection()

        cur = conn.cursor()

        cur.execute("""
            SELECT
                courtroomid,
                courtroomno,
                capacity,
                availability
            FROM courtroom
            WHERE courtid = %s
        """, (courtid,))

        rows = cur.fetchall()

        result = []

        for row in rows:
            result.append({
                "id": row[0],
                "name": f"CourtRoom {row[0]}",
                "number": row[1],
                "capacity": row[2],
                "status": row[3]
            })

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if conn:
            conn.close()