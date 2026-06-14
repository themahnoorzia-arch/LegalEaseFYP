import os
from flask import jsonify, request, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from blueprints.users import users_bp
from db.db import SessionLocal
from models import Lawyer
from models import Courtregistrar, Court, Caseparticipant, Judge, Judge
from db.db import get_pg_connection
import psycopg2
import psycopg2.extras



# ---------------------------------------------------
# GET LAWYER PROFILE
# ---------------------------------------------------
@users_bp.route("/api/lawyerprofile", methods=["GET"])
@login_required
def get_lawyer_profile():
    db = SessionLocal()

    try:
        user_id = current_user.userid

        lawyer = (
            db.query(Lawyer)
            .filter_by(userid=user_id)
            .first()
        )

        if not lawyer:
            return jsonify(
                success=False,
                message="Profile not found"
            ), 404

        return jsonify(
            success=True,
            data={
                "firstName": current_user.firstname,
                "lastName": current_user.lastname,
                "email": current_user.email,
                "phone": current_user.phoneno,
                "specialization": lawyer.specialization,
                "cnic": current_user.cnic,
                "dob": (
                    current_user.dob.isoformat()
                    if current_user.dob
                    else ""
                ),
                "barLicense": lawyer.barlicenseno,
                "experience": lawyer.experienceyears,
            },
        )

    finally:
        db.close()


# ---------------------------------------------------
# UPDATE LAWYER PROFILE
# ---------------------------------------------------
@users_bp.route("/api/lawyerprofile", methods=["PUT"])
@login_required
def update_lawyer_profile():
    db = SessionLocal()

    try:
        user_id = current_user.userid

        lawyer = (
            db.query(Lawyer)
            .filter_by(userid=user_id)
            .first()
        )

        if not lawyer:
            return jsonify(
                success=False,
                message="Profile not found"
            ), 404

        data = request.get_json()

        lawyer.specialization = data.get(
            "specialization",
            lawyer.specialization,
        )

        lawyer.barlicenseno = data.get(
            "barLicense",
            lawyer.barlicenseno,
        )

        lawyer.experienceyears = data.get(
            "experience",
            lawyer.experienceyears,
        )

        db.commit()

        return jsonify(
            success=True,
            message="Profile updated successfully",
        )

    except Exception as e:
        db.rollback()

        return jsonify(
            success=False,
            message=str(e),
        ), 500

    finally:
        db.close()


@users_bp.route("/api/registrarprofile", methods=["GET"])
@login_required
def get_registrar_profile():
    conn = None

    try:
        conn = get_pg_connection()

        cur = conn.cursor(
            cursor_factory=psycopg2.extras.DictCursor
        )

        cur.execute("""
            SELECT
                r.position,
                c.courtname AS courtname
            FROM courtregistrar r
            JOIN court c
                ON r.courtid = c.courtid
            WHERE r.userid = %s
        """, (current_user.userid,))

        registrar = cur.fetchone()

        if not registrar:
            return jsonify(
                success=False,
                message="Registrar profile not found"
            ), 404

        return jsonify(
            success=True,
            data={
                "firstName": current_user.firstname,
                "lastName": current_user.lastname,
                "email": current_user.email,
                "phone": current_user.phoneno,
                "cnic": current_user.cnic,
                "dob": (
                    current_user.dob.isoformat()
                    if current_user.dob else ""
                ),
                "position": registrar["position"],
                "court": registrar["courtname"]
            }
        )

    except Exception as e:
        return jsonify(
            success=False,
            message=str(e)
        ), 500

    finally:
        if conn:
            conn.close()



@users_bp.route("/api/registrarprofile", methods=["PUT"])
@login_required
def update_registrar_profile():
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
                message="Profile not found"
            ), 404

        data = request.get_json()

        registrar.position = data.get(
            "position",
            registrar.position
        )

        db.commit()

        return jsonify(
            success=True,
            message="Profile updated successfully"
        )

    except Exception as e:
        db.rollback()

        return jsonify(
            success=False,
            message=str(e)
        ), 500

    finally:
        db.close()



@users_bp.route("/api/clientprofile", methods=["GET"])
@login_required
def get_client_profile():
    db = SessionLocal()

    try:
        client = (
            db.query(Caseparticipant)
            .filter_by(userid=current_user.userid)
            .first()
        )

        if not client:
            return jsonify(
                success=False,
                message="Client profile not found"
            ), 404

        return jsonify(
            success=True,
            data={
                "firstName": current_user.firstname,
                "lastName": current_user.lastname,
                "email": current_user.email,
                "phone": current_user.phoneno,
                "cnic": current_user.cnic,
                "dob": (
                    current_user.dob.isoformat()
                    if current_user.dob else ""
                ),
                "address": client.address
            }
        )

    finally:
        db.close()



@users_bp.route("/api/clientprofile", methods=["PUT"])
@login_required
def update_client_profile():
    db = SessionLocal()

    try:
        client = (
            db.query(Caseparticipant)
            .filter_by(userid=current_user.userid)
            .first()
        )

        if not client:
            return jsonify(
                success=False,
                message="Profile not found"
            ), 404

        data = request.get_json()

        client.address = data.get(
            "address",
            client.address
        )

        db.commit()

        return jsonify(
            success=True,
            message="Profile updated successfully"
        )

    except Exception as e:
        db.rollback()

        return jsonify(
            success=False,
            message=str(e)
        ), 500

    finally:
        db.close()


@users_bp.route("/api/adminprofile", methods=["GET"])
@login_required
def get_admin_profile():
    if current_user.role != "Admin":
        return jsonify(success=False, message="Admin access required."), 403

    return jsonify(
        success=True,
        data={
            "firstName": current_user.firstname,
            "lastName": current_user.lastname,
            "email": current_user.email,
            "phone": current_user.phoneno,
            "cnic": current_user.cnic,
            "dob": (
                current_user.dob.isoformat()
                if current_user.dob
                else ""
            ),
        },
    )


@users_bp.route("/api/logs", methods=["GET"])
@login_required
def get_logs():
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("""
            SELECT
                l.logid, l.adminid, l.actiontype, l.description,
                l.status, l.actiontimestamp, l.entitytype,
                a.adminid AS admin_adminid
            FROM logtable l
            LEFT JOIN admin a ON l.adminid = a.adminid
            ORDER BY l.actiontimestamp DESC
        """)
        rows = cur.fetchall()

        logs_data = [
            {
                "logid": row["logid"],
                "adminid": row["adminid"],
                "actiontype": row["actiontype"],
                "description": row["description"],
                "status": row["status"],
                "actiontimestamp": row["actiontimestamp"].isoformat()
                if row["actiontimestamp"]
                else None,
                "entitytype": row["entitytype"],
                "admin": {"adminid": row["admin_adminid"]},
            }
            for row in rows
        ]

        cur.close()
        return jsonify(logs_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()


@users_bp.route("/api/logs/activity", methods=["GET"])
@login_required
def get_dashboard_activity_logs():
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("""
            SELECT
                l.description,
                l.entitytype,
                l.actiontimestamp
            FROM logtable l
            WHERE l.entitytype IN (
                'case', 'prosecutor', 'casehistory',
                'finaldecision', 'lawyer', 'judge'
            )
            ORDER BY l.actiontimestamp DESC
            LIMIT 7
        """)
        rows = cur.fetchall()

        activity_logs = [
            {
                "activity": row["description"],
                "type": row["entitytype"],
                "timestamp": row["actiontimestamp"].strftime("%Y-%m-%d %I:%M %p"),
            }
            for row in rows
        ]

        cur.close()
        return jsonify(activity_logs), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()


@users_bp.route("/api/clientdocuments", methods=["GET"])
@login_required
def get_client_documents():
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT
                d.documentid,
                d.documenttitle,
                to_char(d.uploaddate, 'YYYY-MM-DD'),
                d.documenttype,
                d.filepath,
                d.uploaddate
            FROM caseparticipant cp
            JOIN caseparticipantaccess cpa ON cp.participantid = cpa.participantid
            JOIN documentcase dc ON dc.caseid = cpa.caseid
            JOIN documents d ON d.documentid = dc.documentid
            WHERE cp.userid = %s
            ORDER BY d.uploaddate DESC
            """,
            (current_user.userid,),
        )
        documents = [
            {
                "id": row[0],
                "title": row[1],
                "uploadDate": row[2],
                "documenttype": row[3],
                "fileType": row[3],
                "path": row[4],
            }
            for row in cur.fetchall()
        ]
        return jsonify(success=True, documents=documents), 200
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    finally:
        if conn:
            conn.close()


@users_bp.route("/api/judgeprofile", methods=["PUT"])
@login_required
def update_judge_profile():
    if current_user.role != "Judge":
        return jsonify(success=False, message="Judge access required."), 403

    data = request.get_json() or {}
    db = SessionLocal()
    try:
        judge = db.query(Judge).filter_by(userid=current_user.userid).first()
        if not judge:
            return jsonify(success=False, message="Judge profile not found"), 404

        if data.get("firstName"):
            current_user.firstname = data.get("firstName")
        if data.get("lastName"):
            current_user.lastname = data.get("lastName")
        if data.get("email"):
            current_user.email = data.get("email")
        if data.get("phone"):
            current_user.phoneno = data.get("phone")
        if data.get("cnic"):
            current_user.cnic = data.get("cnic")
        if data.get("dob"):
            current_user.dob = data.get("dob")
        if data.get("position") is not None:
            judge.position = data.get("position")
        if data.get("specialization") is not None:
            judge.specialization = data.get("specialization")
        exp = data.get("experience") or data.get("expyears")
        if exp is not None:
            try:
                judge.expyears = int(exp)
            except (TypeError, ValueError):
                pass

        db.commit()
        return jsonify(success=True, message="Profile updated successfully"), 200
    except Exception as e:
        db.rollback()
        return jsonify(success=False, message=str(e)), 500
    finally:
        db.close()


@users_bp.route("/api/judgeprofile", methods=["GET"])
@login_required
def get_judge_profile():
    db = SessionLocal()
    try:
        judge = db.query(Judge).filter_by(userid=current_user.userid).first()
        if not judge:
            return jsonify(success=False, message="Judge profile not found"), 404

        return jsonify(
            success=True,
            data={
                "firstName": current_user.firstname,
                "lastName": current_user.lastname,
                "email": current_user.email,
                "phone": current_user.phoneno,
                "cnic": current_user.cnic,
                "dob": (
                    current_user.dob.isoformat()
                    if current_user.dob
                    else ""
                ),
                "position": judge.position,
                "appointmentdate": judge.appointmentdate,
                "expyears": judge.expyears,
                "specialization": judge.specialization,
            },
        ), 200
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    finally:
        db.close()


# ---------------------------------------------------
# PROFILE PHOTO UPLOAD / SERVE
# ---------------------------------------------------
_PHOTO_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads', 'profile_photos')
_ALLOWED_IMG = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


@users_bp.route("/api/profile/photo", methods=["POST"])
@login_required
def upload_profile_photo():
    if 'photo' not in request.files:
        return jsonify({"message": "No file provided"}), 400
    file = request.files['photo']
    if not file or file.filename == '':
        return jsonify({"message": "Empty filename"}), 400
    ext = os.path.splitext(secure_filename(file.filename))[1].lower()
    if ext not in _ALLOWED_IMG:
        return jsonify({"message": "Only image files are allowed"}), 400
    os.makedirs(_PHOTO_DIR, exist_ok=True)
    # Remove any existing photo for this user first
    for old_ext in _ALLOWED_IMG:
        old_path = os.path.join(_PHOTO_DIR, f"{current_user.userid}{old_ext}")
        if os.path.exists(old_path):
            os.remove(old_path)
    filename = f"{current_user.userid}{ext}"
    file.save(os.path.join(_PHOTO_DIR, filename))
    return jsonify({"message": "Photo uploaded", "url": f"/api/profile/photo/{current_user.userid}"}), 200


@users_bp.route("/api/profile/photo/me", methods=["GET"])
@login_required
def get_my_profile_photo():
    return get_profile_photo(current_user.userid)


@users_bp.route("/api/profile/photo/<int:user_id>", methods=["GET"])
def get_profile_photo(user_id):
    for ext in _ALLOWED_IMG:
        path = os.path.join(_PHOTO_DIR, f"{user_id}{ext}")
        if os.path.exists(path):
            return send_file(os.path.abspath(path))
    return jsonify({"message": "No photo found"}), 404