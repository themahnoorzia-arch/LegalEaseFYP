from flask import request, jsonify, session
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)

from sqlalchemy import text

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from blueprints.auth import auth_bp
from db.db import SessionLocal
from models import (
    Users,
    Lawyer,
    Judge,
    Admin,
    Courtregistrar,
    Caseparticipant,
)


def _verify_password(stored_password, provided_password):
    """Accept hashed passwords and legacy plain-text rows in the database."""
    if not stored_password:
        return False
    if stored_password.startswith(("scrypt:", "pbkdf2:")):
        return check_password_hash(stored_password, provided_password)
    return stored_password == provided_password


def _sync_user_id_sequence(db):
    """Keep PostgreSQL userid sequence aligned with existing rows."""
    db.execute(
        text(
            "SELECT setval("
            "pg_get_serial_sequence('users', 'userid'), "
            "COALESCE((SELECT MAX(userid) FROM users), 0)"
            ")"
        )
    )


# ------------------------------------------------------------------
# SIGNUP
# ------------------------------------------------------------------
@auth_bp.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json()

    firstname = data.get("firstname")
    lastname = data.get("lastname")
    email = data.get("email")
    phoneno = data.get("phoneno")
    cnic = data.get("cnic")
    dob = data.get("dob")
    password = data.get("password")
    role = data.get("role", "").strip().lower()

    role_mapping = {
        "courtregistrar": "CourtRegistrar",
        "client": "CaseParticipant",
        "admin": "Admin",
        "lawyer": "Lawyer",
        "judge": "Judge",
    }

    role = role_mapping.get(role, role)

    valid_roles = [
        "Admin",
        "CourtRegistrar",
        "CaseParticipant",
        "Lawyer",
        "Judge",
    ]

    if role not in valid_roles:
        return jsonify({
            "success": False,
            "message": "Invalid role"
        }), 400

    db = SessionLocal()

    try:
        existing = (
            db.query(Users)
            .filter_by(
                firstname=firstname,
                lastname=lastname
            )
            .first()
        )

        if existing:
            return jsonify({
                "success": False,
                "message": "User already exists with the same name"
            }), 400

        hashed_pw = generate_password_hash(password)

        _sync_user_id_sequence(db)

        user = Users(
            firstname=firstname,
            lastname=lastname,
            email=email,
            phoneno=phoneno,
            cnic=cnic,
            dob=dob,
            password=hashed_pw,
            role=role,
        )

        db.add(user)
        db.flush()
        db.commit()

        session["user_id"] = user.userid
        login_user(user)

        return jsonify({
            "success": True,
            "message": "Signup successful. Please complete your profile.",
            "user_id": user.userid,
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({
            "success": False,
            "message": str(e),
        }), 500

    finally:
        db.close()


# ------------------------------------------------------------------
# COMPLETE PROFILE
# ------------------------------------------------------------------
@auth_bp.route("/api/complete-profile", methods=["POST"])
def complete_profile():
    db = SessionLocal()

    try:
        data = request.get_json()

        user_id = data.get("user_id") or session.get("user_id")

        if not user_id:
            return jsonify({
                "message": "User not logged in or session expired."
            }), 401

        user = db.query(Users).get(user_id)

        if not user:
            return jsonify({
                "message": "User not found"
            }), 404

        role_mapping = {
            "courtregistrar": "CourtRegistrar",
            "caseparticipant": "CaseParticipant",
            "admin": "Admin",
            "lawyer": "Lawyer",
            "judge": "Judge",
        }

        role = user.role.lower()
        user.role = role_mapping.get(role, role)

        # ----------------------------------------------------------
        # Client
        # ----------------------------------------------------------
        if user.role == "CaseParticipant":
            address = data.get("address")

            if address:
                client = Caseparticipant(
                    userid=user.userid,
                    address=address,
                )

                db.add(client)
                db.commit()

        # ----------------------------------------------------------
        # Admin
        # ----------------------------------------------------------
        elif user.role == "Admin":
            admin = Admin(userid=user.userid)

            db.add(admin)
            db.commit()

        # ----------------------------------------------------------
        # Lawyer
        # ----------------------------------------------------------
        elif user.role == "Lawyer":

            bar_license = data.get("barLicense")
            experience = data.get("experience")

            try:
                barlicenseno = int(str(bar_license).strip())
                experienceyears = int(experience)
            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "message": "Bar license and experience must be valid numbers.",
                }), 400

            lawyer = Lawyer(
                userid=user.userid,
                barlicenseno=barlicenseno,
                experienceyears=experienceyears,
                specialization=data.get("specialization"),
            )

            db.add(lawyer)
            db.commit()

        # ----------------------------------------------------------
        # Judge
        # ----------------------------------------------------------
        elif user.role == "Judge":

            try:
                expyears = int(data.get("experience"))
            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "message": "Experience must be a valid number.",
                }), 400

            judge = Judge(
                userid=user.userid,
                position=data.get("position"),
                specialization=data.get("specialization"),
                expyears=expyears,
            )

            db.add(judge)
            db.commit()

        # ----------------------------------------------------------
        # Registrar
        # ----------------------------------------------------------
        elif user.role == "CourtRegistrar":

            registrar = Courtregistrar(
                userid=user.userid,
                position=data.get("position"),
            )

            db.add(registrar)
            db.commit()

        login_user(user)

        return jsonify({
            "success": True,
            "message": "Profile completed successfully",
        }), 200

    except Exception as e:
        db.rollback()

        return jsonify({
            "message": f"An error occurred while completing the profile: {str(e)}"
        }), 500

    finally:
        db.close()


# ------------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------------
@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    db = SessionLocal()

    try:
        user = (
            db.query(Users)
            .filter_by(email=email)
            .first()
        )

        if user and _verify_password(user.password, password):
            login_user(user)

            mapped_role = (
                "Client"
                if user.role == "CaseParticipant"
                else user.role
            )

            return jsonify({
                "success": True,
                "message": "Logged in",
                "email": user.email,
                "role": mapped_role,
                "user_id": user.userid,
            }), 200

        return jsonify({
            "success": False,
            "message": "Invalid credentials",
        }), 401

    finally:
        db.close()


# ------------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------------
@auth_bp.route("/api/dashboard", methods=["GET"])
@login_required
def dashboard():
    db = SessionLocal()

    try:
        lawyer = (
            db.query(Lawyer)
            .filter_by(userid=current_user.userid)
            .first()
        )

        specialization = (
            lawyer.specialization
            if lawyer
            else None
        )

        barlicenseno = (
            lawyer.barlicenseno
            if lawyer
            else None
        )

        return jsonify({
            "success": True,
            "user": {
                "username":
                    f"{current_user.firstname} "
                    f"{current_user.lastname}",
                "specialization": specialization,
                "barlicenseno": barlicenseno,
            },
        })

    finally:
        db.close()


# ------------------------------------------------------------------
# LOGOUT
# ------------------------------------------------------------------
@auth_bp.route("/api/logout", methods=["POST"])
@login_required
def logout():
    logout_user()

    return jsonify({
        "success": True,
        "message": "Logged out",
    })