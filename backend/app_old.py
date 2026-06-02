import datetime
from decimal import Decimal
import logging
import os
import traceback
import psycopg2
# fom psycopg.rows import dict_row
from flask import Flask, g, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import aliased
from config import Config
from models import *

# Validate configuration
Config.validate_config()

app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/")
app.config.from_object(Config)

# Database setup
logging.basicConfig(level=logging.DEBUG)
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_pg_connection():
    import psycopg2
    return psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)



# Session and CORS
Session(app)
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    db = SessionLocal()
    user = db.query(Users).get(int(user_id))
    db.close()
    return user

@app.route("/")
def serve():
    return app.send_static_file("index.html")

@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json()
    logging.debug(f"Received data for signup: {data}")

    firstname = data.get("firstname")
    lastname = data.get("lastname")
    email = data.get("email")
    phoneno = data.get("phoneno")
    cnic = data.get("cnic")
    dob = data.get("dob")
    password = data.get("password")
    role = data.get("role", "user").strip().lower()  # Make role lowercase

    logging.debug(f"Processed role: {role}")

    # Role mapping to ensure the correct capitalization in the database
    role_mapping = {
        "courtregistrar": "CourtRegistrar",
        "client": "CaseParticipant",
        "admin": "Admin",
        "lawyer": "Lawyer",
        "judge": "Judge"
    }

    role = role_mapping.get(role, role)  # Get the correct role or default to the input role
    logging.debug(f"Mapped role: {role}")

    valid_roles = ["Admin", "CourtRegistrar", "CaseParticipant", "Lawyer", "Judge"]
    if role not in valid_roles:
        logging.error(f"Invalid role received: {role}")
        return jsonify({"success": False, "message": "Invalid role"}), 400

    db = SessionLocal()
    try:
        # Check if a user with the same username already exists
        existing = db.query(Users).filter_by(firstname=firstname, lastname=lastname).first()
        if existing:
            logging.warning(f"User already exists with firstname: {firstname} and lastname: {lastname}")
            return jsonify({"success": False, "message": "User already exists with the same name"}), 400

        hashed_pw = generate_password_hash(password)

        user = Users(
            firstname=firstname,
            lastname=lastname,
            email=email,
            phoneno=phoneno,
            cnic=cnic,
            dob=dob,
            password=hashed_pw,
            role=role
        )
        db.add(user)
        db.flush()
        db.commit()

        logging.info(f"User created: {user.userid}")
        session['user_id'] = user.userid
        login_user(user)

    except Exception as e:
        db.rollback()
        logging.error(f"Error occurred during sign-up: {str(e)}")
        return jsonify({"message": "An error occurred during sign-up."}), 500

    finally:
        db.close()

    return jsonify({
        "success": True,
        "message": "Signup successful. Please complete your profile.",
        "user_id": user.userid
    }), 201

@app.route('/api/complete-profile', methods=['POST'])
def complete_profile():
    db = SessionLocal()
    try:
        data = request.get_json()
        print(f"Data received: {data}")

        user_id = data.get('user_id') or session.get('user_id')
        if not user_id:
            return jsonify({"message": "User not logged in or session expired."}), 401

        user = db.query(Users).get(user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404


        print(f"User role: {user.role}")
        # Normalize role during profile completion
        role_mapping = {
            "courtregistrar": "CourtRegistrar",
            "caseparticipant": "CaseParticipant",
            "admin": "Admin",
            "lawyer": "Lawyer",
            "judge": "Judge"
        }
        role = user.role.lower()  # Normalize role to lowercase
        user.role = role_mapping.get(role, role)  # Update to correct role case if needed

        # The rest of the profile completion logic remains the same...
        if user.role == 'CaseParticipant':
            address = data.get('address')
            if address:
                client = Caseparticipant(userid=user.userid, address=address)
                db.add(client)
                db.commit()
                print(f"Inserted CaseParticipant: {client}")

        elif user.role == 'Admin':
            admin = Admin(userid=user.userid)
            db.add(admin)
            db.commit()
            print(f"Inserted Admin: {admin}")

        elif user.role == 'Lawyer':
            barlicenseno = data.get('barLicense')  
            experienceyears = data.get('experience')  
            specialization = data.get('specialization')

            if barlicenseno and experienceyears and specialization:
                print("All Lawyer fields present, inserting Lawyer...")
                try:
                    lawyer = Lawyer(
                        userid=user.userid,
                        barlicenseno=barlicenseno,
                        experienceyears=experienceyears,
                        specialization=specialization
                    )
                    db.add(lawyer)
                    db.commit()
                    print(f"Inserted Lawyer: {lawyer}")
                except Exception as e:
                    db.rollback()
                    print(f"Exception occurred while inserting Lawyer: {e}")
            else:
                print("One or more required Lawyer fields are missing.")

        elif user.role == 'Judge':
            position = data.get('position')
            specialization = data.get('specialization')
            experience = data.get('experience')
            if position and specialization and experience:
                judge = Judge(
                    userid=user.userid,
                    position=position,
                    specialization=specialization,
                    expyears=experience
                )
                db.add(judge)
                db.commit()
                print(f"Inserted Judge: {judge}")

        elif user.role == 'CourtRegistrar':
            position = data.get('position')
            if position:
                registrar = Courtregistrar(userid=user.userid, position=position)
                db.add(registrar)
                db.commit()
                print(f"Inserted Court Registrar: {registrar}")

        login_user(user)
        return jsonify({
    "message": "Profile completed successfully",
    "success": True
}), 200

    except Exception as e:
        error_message = str(e)
        print(f"Error occurred: {error_message}")
        db.rollback()
        return jsonify({"message": f"An error occurred while completing the profile: {error_message}"}), 500
    
    finally:
        db.close()
        
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    db = SessionLocal()
    try:
        user = db.query(Users).filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)

            # 🔁 Map CaseParticipant to Client
            mapped_role = "Client" if user.role == "CaseParticipant" else user.role

            return jsonify({
                "success": True,
                "message": "Logged in",
                "email": user.email,
                "role": mapped_role
            }), 200

        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    finally:
        db.close()

@app.route("/api/dashboard", methods=["GET"])
@login_required
def dashboard():
    db = SessionLocal()
    lawyer = db.query(Lawyer).filter_by(userid=current_user.userid).first()
    specialization = lawyer.specialization if lawyer else None
    barlicenseno = lawyer.barlicenseno if lawyer else None
    db.close()

    return jsonify({
        "success": True,
        "user": {
            "username": f"{current_user.firstname} {current_user.lastname}",
            "specialization": specialization,
            "barlicenseno": barlicenseno
        }
    })

@app.route("/api/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"success": True, "message": "Logged out"})

@app.route('/api/lawyerprofile', methods=['GET'])
def get_lawyer_profile():
    db = SessionLocal()
    user_id = current_user.userid  
    
    if not user_id:
        return jsonify(success=False, message="User ID is required."), 400

    lawyer = db.query(Lawyer).filter_by(userid=user_id).first()

    if not lawyer:
        return jsonify(success=False, message="Profile not found"), 404

    return jsonify(success=True, data={
        'firstName': current_user.firstname,
        'lastName': current_user.lastname,
        'email': current_user.email,
        'phone': current_user.phoneno,
        'specialization': lawyer.specialization,
        'cnic': current_user.cnic,
        'dob': current_user.dob.isoformat() if current_user.dob else '',
        'barLicense': lawyer.barlicenseno,
        'experience': lawyer.experienceyears
    })

@app.route('/api/lawyerprofile', methods=['PUT'])
def update_lawyer_profile():
    db = SessionLocal()
    user_id = current_user.userid

    if not user_id:
        return jsonify(success=False, message="User ID is required."), 400

    data = request.get_json()
    lawyer = db.query(Lawyer).filter_by(userid=user_id).first()

    if not lawyer:
        return jsonify(success=False, message="Profile not found"), 404

    try:
        lawyer.specialization = data.get('specialization', lawyer.specialization)
        lawyer.barlicenseno = data.get('barLicense', lawyer.barlicenseno)
        lawyer.experienceyears = data.get('experience', lawyer.experienceyears)

        db.commit()
        return jsonify(success=True, message="Profile updated successfully")

    except Exception as e:
        db.rollback()
        return jsonify(success=False, message=str(e)), 500
    

@app.route('/api/registrarprofile', methods=['PUT'])
# @log_action(action_type="Update",entity_type="Court Registrar")
def update_registrar_profile():
    db = SessionLocal()
    user_id = current_user.userid

    if not user_id:
        return jsonify(success=False, message="User ID is required."), 400

    data = request.get_json()
    registrar = db.query(Courtregistrar).filter_by(userid=user_id).first()

    if not registrar:
        return jsonify(success=False, message="Profile not found"), 404

    try:
        registrar.position = data.get('position', registrar.position)

        db.commit()
        return jsonify(success=True, message="Profile updated successfully")

    except Exception as e:
        db.rollback()
        return jsonify(success=False, message=str(e)), 500
    
@app.route('/api/clientprofile', methods=['PUT'])
def update_client_profile():
    db = SessionLocal()
    user_id = current_user.userid

    if not user_id:
        return jsonify(success=False, message="User ID is required."), 400

    data = request.get_json()
    client = db.query(Caseparticipant).filter_by(userid=user_id).first()

    if not client:
        return jsonify(success=False, message="Profile not found"), 404

    try:
        client.address = data.get('address', client.address)
        

        db.commit()
        return jsonify(success=True, message="Profile updated successfully")

    except Exception as e:
        db.rollback()
        return jsonify(success=False, message=str(e)), 500
    
    
@app.route('/api/judges', methods=['GET'])
@login_required
def get_judges_for_court():
    user_id = current_user.userid  # your user id attribute

    conn = get_pg_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # 1. Get court_id from courtregistrar using user_id
            cur.execute("SELECT courtid FROM courtregistrar WHERE userid = %s", (user_id,))
            court = cur.fetchone()
            if not court:
                return jsonify({"error": "Court Registrar not found"}), 404
            court_id = court['courtid']

            # 2. Get judges assigned to this court via judgeworksin
            cur.execute("""
                SELECT j.judgeid, u.firstname, u.lastname, j.position, j.expyears, j.appointmentdate, j.specialization
                FROM judge j
                JOIN users u ON u.userid = j.userid
                JOIN judgeworksin jw ON jw.judgeid = j.judgeid
                WHERE jw.courtid = %s
            """, (court_id,))
            judges = cur.fetchall()

            response = []
            for judge in judges:
                # 3. Get assigned case titles from judgeaccess + cases
                cur.execute("""
                    SELECT c.title
                    FROM judgeaccess ja
                    JOIN cases c ON ja.caseid = c.caseid
                    WHERE ja.judgeid = %s
                """, (judge['judgeid'],))
                cases = cur.fetchall()
                assigned_titles = [c['title'] for c in cases]

                full_name = f"{judge['firstname']} {judge['lastname']}"

                response.append({
                    "judgeid": judge['judgeid'],
                    "name": full_name,
                    "position": judge['position'],
                    "expyears": judge['expyears'],
                    "appointmentdate": judge['appointmentdate'].isoformat() if judge['appointmentdate'] else None,
                    "specialization": judge['specialization'],
                    "assigned_cases": assigned_titles
                })

        return jsonify({"judges": response})

    finally:
        conn.close()
        
@app.route('/api/judge', methods=['PUT'])
@login_required
def update_judge():
    data = request.get_json()
    if not data:
        return jsonify(success=False, message="No data provided"), 400

    full_name = data.get('name', '').strip()
    if not full_name:
        return jsonify(success=False, message="Judge name is required"), 400

    # Split name; if only one part given, last name = ''
    name_parts = full_name.split()
    firstname = name_parts[0]
    lastname = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

    # Optional fields for further filtering
    appointmentdate = data.get('appointmentDate')
    position = data.get('position')

    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Find userid in users table by firstname and lastname
        cur.execute("""
            SELECT userid FROM users
            WHERE firstname = %s AND lastname = %s
        """, (firstname, lastname))
        user_row = cur.fetchone()
        if not user_row:
            cur.close()
            conn.close()
            return jsonify(success=False, message="Judge user not found"), 404
        userid = user_row['userid']

        # Build query to find judge record
        query = "SELECT * FROM judge WHERE userid = %s"
        params = [userid]

        # Add optional filters if provided
        if appointmentdate:
            query += " AND appointmentdate = %s"
            params.append(appointmentdate)
        if position:
            query += " AND position = %s"
            params.append(position)

        cur.execute(query, params)
        judge = cur.fetchone()
        if not judge:
            cur.close()
            conn.close()
            return jsonify(success=False, message="Judge profile not found"), 404

        # Use new values from frontend or fallback to existing values
        specialization = data.get('specialization', judge['specialization'])
        appointmentdate_new = data.get('appointmentDate', judge['appointmentdate'])
        expyears = data.get('experience', judge['expyears'])
        position_new = data.get('position', judge['position'])

        # Update judge profile
        cur.execute("""
            UPDATE judge
            SET specialization = %s,
                appointmentdate = %s,
                expyears = %s,
                position = %s
            WHERE userid = %s
        """, (specialization, appointmentdate_new, expyears, position_new, userid))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify(success=True, message="Profile updated successfully")

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify(success=False, message=str(e)), 500


@app.route('/api/court', methods=['POST'])
@login_required
def add_court():
    db = SessionLocal()
    try:
        data = request.get_json()

        courtname = data.get('name')
        court_type = data.get('courtType')
        location = data.get('address')

        if not courtname or not court_type or not location:
            return jsonify({'status': 'error', 'message': 'All fields (courtname, type, location) are required'}), 400

        new_court = Court(courtname=courtname, type=court_type, location=location)
        db.add(new_court)
        db.flush()  

        
        if current_user.role == 'CourtRegistrar':
            registrar = db.query(Courtregistrar).filter_by(userid=current_user.userid).first()
            if registrar:
                registrar.courtid = new_court.courtid  # Associate court
                print(f"Linked court ID {new_court.courtid} to registrar {registrar.courtid}")
            else:
                return jsonify({'status': 'error', 'message': 'CourtRegistrar profile not found'}), 404

        db.commit()

        return jsonify({'status': 'success', 'message': 'Court added and linked to registrar', 'court_id': new_court.courtid}), 201

    except Exception as e:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        db.close()
        
@app.route('/api/registrarprofile', methods=['GET'])
@login_required
def get_registrar_profile():
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        user_id = current_user.userid

        # Join courtregistrar with court to get court name
        cur.execute("""
            SELECT r.position, c.courtname AS courtname
            FROM courtregistrar r
            JOIN court c ON r.courtid = c.courtid
            WHERE r.userid = %s
        """, (user_id,))
        registrar = cur.fetchone()

        if not registrar:
            cur.close()
            conn.close()
            return jsonify(success=False, message="Registrar profile not found"), 404

        data = {
            'firstName': current_user.firstname,
            'lastName': current_user.lastname,
            'email': current_user.email,
            'phone': current_user.phoneno,
            'cnic': current_user.cnic,
            'dob': current_user.dob.isoformat() if current_user.dob else '',
            'position': registrar['position'],
            'court': registrar['courtname']
        }

        cur.close()
        conn.close()

        return jsonify(success=True, data=data), 200

    except Exception as e:
        if conn:
            conn.close()
        return jsonify(success=False, message=str(e)), 500

@app.route('/api/court', methods=['GET'])
@login_required
def get_court_for_registrar():
    db = SessionLocal()
    try:
        registrar = db.query(Courtregistrar).filter_by(userid=current_user.userid).first()
        if not registrar:
            return jsonify(success=False, message="Registrar profile not found"), 404

        if not registrar.courtid:
            return jsonify(success=False, message="Registrar is not assigned to any court"), 404

        court = db.query(Court).get(registrar.courtid)
        if not court:
            return jsonify(success=False, message="Court not found"), 404

        return jsonify(success=True, data={
            "id":court.courtid,
            'courtname': court.courtname,
            'type': court.type,
            'location': court.location
        }), 200

    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    finally:
        db.close()
@app.route('/api/payments', methods=['GET'])
@login_required
def get_payments():
    db = SessionLocal()
    try:
        if current_user.role == 'Lawyer':
            lawyer = db.query(Lawyer).filter_by(userid=current_user.userid).first()
            if not lawyer:
                return jsonify({'status': 'error', 'message': 'Lawyer profile not found'}), 404

            payments = (
                db.query(Payments)
                .filter_by(lawyerid=lawyer.lawyerid)
                .join(Cases, Payments.caseid == Cases.caseid)
                .join(t_courtaccess, Payments.caseid == t_courtaccess.c.caseid)
                .join(Court, t_courtaccess.c.courtid == Court.courtid)
                .with_entities(
                    Payments.paymentdate,
                    Cases.title.label("casename"),
                    Payments.purpose,
                    Payments.balance,
                    Payments.mode,
                    Payments.paymenttype,
                    Payments.status,
                    Court.courtname
                )
                .all()
            )

        elif current_user.role == 'CourtRegistrar':
            court_registrar = db.query(Courtregistrar).filter_by(userid=current_user.userid).first()
            if not court_registrar:
                return jsonify({'status': 'error', 'message': 'Court registrar profile not found'}), 404
            
            court_id = court_registrar.courtid
            
            payments = (
                db.query(Payments)
                .join(Cases, Payments.caseid == Cases.caseid)
                .join(t_courtaccess, t_courtaccess.c.caseid == Cases.caseid)
                .filter(t_courtaccess.c.courtid == court_id)
                .with_entities(
                    Payments.paymentdate,
                    Cases.title.label("casename"),
                    Payments.purpose,
                    Payments.balance,
                    Payments.mode,
                    Payments.paymenttype,
                    Payments.status,
                    Court.courtname  # ⚠️ Court must be joined here too
                )
                .join(Court, t_courtaccess.c.courtid == Court.courtid)  # <-- Add this join
                .all()
            )
        else:
            return jsonify({'status': 'error', 'message': 'Unauthorized role'}), 403

        result = [
            {
                "paymentdate": str(p.paymentdate),
                "casename": p.casename,
                "purpose": p.purpose,
                "balance": float(p.balance),
                "mode": p.mode,
                "paymenttype": p.paymenttype,
                "status": p.status,
                "courtname": p.courtname
            }
            for p in payments
        ]

        return jsonify({'status': 'success', 'payments': result}), 200


    except Exception as e:
        print("❌ Exception in /api/payments:", e)
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        db.close()

@app.route('/api/payments', methods=['POST'])
@login_required
def create_payment():
    data = request.get_json()

    casename = data.get('casename')
    purpose = data.get('purpose')
    balance = data.get('balance')
    mode = data.get('mode')
    paymenttype = data.get('paymenttype')
    paymentdate = data.get('paymentdate') or datetime.date.today()

    if not all([casename, purpose, balance, mode, paymenttype]):
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 1. Get lawyer ID for current user
        cur.execute("SELECT lawyerid FROM lawyer WHERE userid = %s", (current_user.userid,))
        lawyer_row = cur.fetchone()
        if not lawyer_row:
            return jsonify({'message': 'Lawyer not found'}), 404
        lawyerid = lawyer_row['lawyerid']

        # 2. Get case ID by title
        cur.execute("SELECT caseid FROM cases WHERE title = %s", (casename,))
        case_row = cur.fetchone()
        if not case_row:
            return jsonify({'message': 'Case not found'}), 404
        caseid = case_row['caseid']

        # 3. Get court ID from courtaccess
        cur.execute("SELECT courtid FROM courtaccess WHERE caseid = %s", (caseid,))
        court_row = cur.fetchone()
        if not court_row:
            return jsonify({'message': 'Court access entry not found'}), 404
        courtid = court_row['courtid']

        # 4. Insert into payments
        cur.execute("""
            INSERT INTO payments (mode, purpose, balance, paymentdate, lawyerid, caseid, courtid, paymenttype)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            mode,
            purpose,
            Decimal(balance),
            paymentdate,
            lawyerid,
            caseid,
            courtid,
            paymenttype
        ))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            'message': 'Payment recorded successfully',
            'payment': {
                'paymentdate': str(paymentdate),
                'casename': casename,
                'purpose': purpose,
                'balance': float(balance),
                'mode': mode,
                'paymenttype': paymenttype
            }
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'message': str(e)}), 500
        
@app.route('/api/clientprofile', methods=['GET'])
@login_required
def get_client_profile():
    db = SessionLocal()
    try:
        user_id = current_user.userid

        client = db.query(Caseparticipant).filter_by(userid=user_id).first()

        if not client:
            return jsonify(success=False, message="Client profile not found"), 404

        return jsonify(success=True, data={
            'firstName': current_user.firstname,
            'lastName': current_user.lastname,
            'email': current_user.email,
            'phone': current_user.phoneno,
            'cnic': current_user.cnic,
            'dob': current_user.dob.isoformat() if current_user.dob else '',
            'address':client.address  
        }), 200

    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

    finally:
        db.close()

@app.route('/api/judgeprofile', methods=['GET'])
@login_required
def get_judge_profile():
    db = SessionLocal()
    try:
        user_id = current_user.userid

        judge = db.query(Judge).filter_by(userid=user_id).first()

        if not judge:
            return jsonify(success=False, message="Judge profile not found"), 404

        return jsonify(success=True, data={
            'firstName': current_user.firstname,
            'lastName': current_user.lastname,
            'email': current_user.email,
            'phone': current_user.phoneno,
            'cnic': current_user.cnic,
            'dob': current_user.dob.isoformat() if current_user.dob else '',
            'position': judge.position,
            'appointmentdate':judge.appointmentdate,
            'expyears':judge.expyears,
            'specialization':judge.specialization
        }), 200

    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

    finally:
        db.close()
@app.route("/api/prosecutors", methods=["GET"])
@login_required
def get_prosecutors():
    print("Endpoint /api/prosecutors called")
    conn = None
    try:
        conn = get_pg_connection()
        print("Database connection established")

        user_id = current_user.userid
        print(f"Current user ID: {user_id}")

        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Step 1: Get court ID of the logged-in registrar
            print("Fetching registrar's court ID...")
            cur.execute("""
                SELECT courtid 
                FROM courtregistrar 
                WHERE userid = %s
            """, (user_id,))
            row = cur.fetchone()

            if not row:
                print("Registrar not found for user")
                return jsonify({"error": "Registrar not found"}), 404

            court_id = row["courtid"]
            print(f"Registrar's court ID: {court_id}")

            # Step 2: Fetch all prosecutors
            print("Fetching all prosecutors...")
            cur.execute("SELECT * FROM prosecutor")
            prosecutors = cur.fetchall()
            print(f"Total prosecutors fetched: {len(prosecutors)}")

            # Step 3: Fetch case assignments only where courtaccess.courtid = registrar's court_id
            print("Fetching case assignments for registrar's court...")
            cur.execute("""
                SELECT 
                    p.prosecutorid, 
                    c.title
                FROM 
                    prosecutorassign pa
                JOIN 
                    prosecutor p ON pa.prosecutorid = p.prosecutorid
                JOIN 
                    cases c ON pa.caseid = c.caseid
                JOIN 
                    courtaccess ca ON ca.caseid = c.caseid
                WHERE 
                    ca.courtid = %s
            """, (court_id,))
            assignments = cur.fetchall()
            print(f"Filtered assignments fetched: {len(assignments)}")

        # Step 4: Build map from prosecutor to assigned case titles
        prosecutor_case_map = {}
        for row in assignments:
            pid = row["prosecutorid"]
            prosecutor_case_map.setdefault(pid, []).append(row["title"])

        # Step 5: Format response
        result = []
        for p in prosecutors:
            assigned = prosecutor_case_map.get(p["prosecutorid"], [])
            result.append({
                "id": p["prosecutorid"],
                "name": p["name"],
                "experience": p["experience"],
                "status": p["status"],
                "assignedCases": assigned
            })

        print("Returning prosecutors with court-specific assignments")
        return jsonify({"prosecutors": result}), 200

    except Exception as e:
        print("Error fetching prosecutors:", str(e))
        return jsonify({"error": "Internal server error"}), 500

    finally:
        if conn:
            conn.close()
            print("Database connection closed")

@app.route("/api/prosecutor", methods=['POST'])
@login_required
def create_prosecutor():
    data = request.get_json()
    name = data.get('name')
    experience = data.get('experience')
    status = data.get('status')
    case_names = data.get('case_names', [])

    if not name or experience is None or status is None:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 1. Insert into prosecutor table
        cur.execute("""
            INSERT INTO prosecutor (name, experience, status)
            VALUES (%s, %s, %s)
            RETURNING prosecutorid
        """, (name, experience, status))
        prosecutor_row = cur.fetchone()
        prosecutor_id = prosecutor_row['prosecutorid']

        # 2. If case names provided, link to cases
        if case_names:
            # Fetch case IDs from cases table
            cur.execute("""
                SELECT caseid FROM cases
                WHERE title = ANY(%s)
            """, (case_names,))
            case_rows = cur.fetchall()
            case_ids = [row['caseid'] for row in case_rows]

            # Insert into t_prosecutorassign
            for cid in case_ids:
                cur.execute("""
                    INSERT INTO prosecutorassign (prosecutor_id, case_id)
                    VALUES (%s, %s)
                """, (prosecutor_id, cid))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "id": prosecutor_id,
            "name": name,
            "experience": experience,
            "status": status,
            "assigned_cases": case_names
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/prosecutor", methods=['PUT'])
@login_required
def update_prosecutor():
    data = request.get_json()
    prosecutor_id = data.get('id')
    name = data.get('name')
    experience = data.get('experience')
    status = data.get('status')
    case_names = data.get('case_names', [])

    if not prosecutor_id or not name:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Update prosecutor record
        cur.execute("""
            UPDATE prosecutor
            SET name = %s, experience = %s, status = %s
            WHERE prosecutorid = %s
        """, (name, experience, status, prosecutor_id))

        # Delete existing case assignments
        cur.execute("DELETE FROM prosecutorassign WHERE prosecutor_id = %s", (prosecutor_id,))

        # Insert updated case assignments
        if case_names:
            cur.execute("""
                SELECT caseid FROM cases
                WHERE title = ANY(%s)
            """, (case_names,))
            case_rows = cur.fetchall()
            case_ids = [row['caseid'] for row in case_rows]

            for cid in case_ids:
                cur.execute("""
                    INSERT INTO prosecutorassign (prosecutor_id, case_id)
                    VALUES (%s, %s)
                """, (prosecutor_id, cid))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "message": "Prosecutor updated successfully"})

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/prosecutor/<int:prosecutor_id>", methods=['DELETE'])
@login_required
def delete_prosecutor(prosecutor_id):
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        # Delete assignments
        cur.execute("DELETE FROM prosecutorassign WHERE prosecutorid = %s", (prosecutor_id,))
        # Delete prosecutor
        cur.execute("DELETE FROM prosecutor WHERE prosecutorid = %s", (prosecutor_id,))

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Prosecutor deleted successfully"})

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({"error": str(e)}), 500


@app.route('/api/courtrooms', methods=['POST'])
@login_required
def create_courtroom():
    data = request.get_json()

    number = data.get('number')
    capacity = data.get('capacity')
    availability = data.get('availability')

    if not all([number, capacity]):
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        # Get courtid for current registrar user
        cur.execute("""
            SELECT courtid FROM courtregistrar WHERE userid = %s
        """, (current_user.userid,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return jsonify({'message': 'Court registrar or court not found'}), 404
        courtid = row[0]

        # Insert into courtroom table
        cur.execute("""
            INSERT INTO courtroom (courtroomno, capacity, availability, courtid)
            VALUES (%s, %s, %s, %s)
        """, (number, capacity, availability, courtid))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'message': 'Courtroom created successfully'}), 201

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'message': str(e)}), 500
    

@app.route('/api/courtrooms/<int:courtroom_id>', methods=['PUT'])
@login_required
def update_courtroom(courtroom_id):
    data = request.get_json()

    number = data.get('number')
    capacity = data.get('capacity')
    availability = data.get('status')

    if not all([number, capacity, availability]):
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        #verify courtroom exists 
        cur.execute("SELECT 1 FROM courtroom WHERE courtroomid = %s", (courtroom_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'message': 'Courtroom not found'}), 404

        # Update courtroom record
        cur.execute("""
            UPDATE courtroom
            SET courtroomno = %s,
                capacity = %s,
                availability = %s
            WHERE courtroomid = %s
        """, (number, capacity, availability, courtroom_id))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'message': 'Courtroom updated successfully'})

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'message': str(e)}), 500
    
@app.route('/api/courtrooms/<int:courtroom_id>', methods=['DELETE'])
@login_required
def delete_courtroom(courtroom_id):
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        #   verify courtroom exists
        cur.execute("SELECT 1 FROM courtroom WHERE courtroomid = %s", (courtroom_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'message': 'Courtroom not found'}), 404

        # Delete courtroom
        cur.execute("DELETE FROM courtroom WHERE courtroomid = %s", (courtroom_id,))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'message': 'Courtroom deleted successfully'})

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'message': str(e)}), 500


@app.route('/api/courtrooms', methods=['GET'])
@login_required
def get_courtrooms():
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT number AS courtroomno, capacity, status
            FROM courtroom
        """)
        rows = cur.fetchall()

        result = [
            {
                'number': row['courtroomno'],
                'capacity': row['capacity'],
                'status': row['status']
            }
            for row in rows
        ]

        cur.close()
        conn.close()
        return jsonify({'courtrooms': result}), 200

    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'message': str(e)}), 500

@app.route('/api/cases', methods=['POST'])
@login_required
def create_case():
    conn = None
    try:
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        casetype = data.get('casetype')  # frontend sends camelCase
        filingdate = data.get('filingdate') or datetime.date.today()
        status = data.get('status', 'Open')
        courtname = data.get('courtname')  # <-- fix this
        fullname = data.get('clientName', '').strip()  # <-- fine if coming from frontend

        print("DEBUG RAW DATA:", data)
        print("DEBUG PARSED VALUES:", {
    'title': title,
    'casetype': casetype,
    'courtname': courtname,
    'fullname': fullname
})
        if not title or not casetype or not courtname or not fullname:
            return jsonify({'message': 'Missing required fields'}), 400

        # Split full name into first and last name
        name_parts = fullname.split()
        if len(name_parts) < 2:
            return jsonify({'message': 'Please provide full name as "First Last"'}), 400
        firstname, lastname = name_parts[0], ' '.join(name_parts[1:])

        conn = get_pg_connection()
        cur = conn.cursor()

        # 1. Get courtid
        cur.execute("SELECT courtid FROM court WHERE courtname = %s", (courtname,))
        court_result = cur.fetchone()
        if not court_result:
            return jsonify({'message': 'Court not found'}), 404
        courtid = court_result[0]

        # 2. Insert into cases
        cur.execute("""
            INSERT INTO cases (title, description, casetype, filingdate, status)
            VALUES (%s, %s, %s, %s, 'Pending')
            RETURNING caseid
        """, (title, description, casetype, filingdate))
        caseid = cur.fetchone()[0]

        # 3. Insert into courtaccess
        cur.execute("""
            INSERT INTO courtaccess (courtid, caseid)
            VALUES (%s, %s)
        """, (courtid, caseid))

        # 4. Fetch userid from users
        cur.execute("""
            SELECT userid FROM users WHERE firstname = %s AND lastname = %s
        """, (firstname, lastname))
        user_result = cur.fetchone()
        if not user_result:
            return jsonify({'message': 'User not found for provided full name'}), 404
        userid = user_result[0]

        # 5. Fetch participantid from caseparticipant using userid
        cur.execute("""
            SELECT participantid FROM caseparticipant WHERE userid = %s
        """, (userid,))
        participant_result = cur.fetchone()
        if not participant_result:
            return jsonify({'message': 'Participant not found for user'}), 404
        participantid = participant_result[0]

        # 6. Insert into caseparticipantaccess
        cur.execute("""
            INSERT INTO caseparticipantaccess (participantid, caseid)
            VALUES (%s, %s)
        """, (participantid, caseid))

        conn.commit()
        return jsonify({'message': 'Case created successfully', 'case_id': caseid}), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'message': str(e)}), 500

    finally:
        if conn:
            conn.close()

        
@app.route('/api/courtrooms/<int:courtid>', methods=['GET'])
@login_required
def get_courtrooms_by_court(courtid):
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        query = """
            SELECT courtroomid, courtroomno, capacity, availability
            FROM courtroom
            WHERE courtid = %s
        """
        cur.execute(query, (courtid,))
        rows = cur.fetchall()

        result = [
            {
                'id': row[0],
                'name': "CourtRoom " + str(row[0]),
                'number': row[1],
                'capacity': row[2],
                'status': row[3]
            }
            for row in rows
        ]

        cur.close()
        return jsonify({'success': True, 'data': result}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        if conn:
            conn.close()
@app.route('/api/cases', methods=['GET'])
@login_required
def get_cases():
    db = SessionLocal()
    try:
        # Filter parameters
        query_params = request.args
        status = query_params.get('status')
        casetype = query_params.get('casetype')
        title = query_params.get('title')

        userid = current_user.userid
        role = current_user.role

        query = db.query(Cases)

        # Role-based access
        if role == 'Lawyer':
            lawyer = db.query(Lawyer).filter_by(userid=userid).first()
            if not lawyer:
                return jsonify({'message': 'Lawyer profile not found'}), 404

            query = query.join(Cases.lawyer).filter(Lawyer.lawyerid == lawyer.lawyerid)
            cases = query.distinct().all()

            result = []
            for c in cases:
                # Court name(s)
                court_names = [court.courtname for court in c.court if court.courtname]
                court_name_str = ', '.join(court_names) if court_names else 'N/A'

                # Get prosecutor name by joining prosecutorassign and prosecutor tables using caseid
                prosecutor_name = 'N/A'
                prosecutor_assign_rows = db.execute(
                t_prosecutorassign.select().where(t_prosecutorassign.c.caseid == c.caseid)
                ).fetchall()

                if prosecutor_assign_rows:
        # Assuming one prosecutor per case, or take the first
                    prosecutorid = prosecutor_assign_rows[0].prosecutorid
                    prosecutor = db.query(Prosecutor).filter_by(prosecutorid=prosecutorid).first()
                    if prosecutor:
                        prosecutor_name = prosecutor.name
                    
                
                # Judge name
                judge_name = ''
                if c.judge:
                    judge = c.judge[0]
                    if judge.users:
                        judge_name = f"{judge.users.firstname or ''} {judge.users.lastname or ''}".strip()

                # Case history
                history = [
                    {
                        'date': h.actiondate.isoformat() if h.actiondate else None,
                        'event': h.actiontaken
                    }
                    for h in c.casehistory
                ]

                # Final decision
                decision_data = {}
                if c.finaldecision:
                    fd = c.finaldecision[0]
                    decision_data = {
                        'decisionId': fd.decisionid,
                        'verdict': fd.verdict or '',
                        'decisionSummary': fd.decisionsummary or '',
                        'decisionDate': fd.decisiondate.isoformat() if fd.decisiondate else ''
                    }

                # Remand status
                remand = db.query(Remands).filter_by(caseid=c.caseid).first()
                remand_status = remand.status if remand else 'N/A'

                # Client name
                client_name = 'N/A'
                access_row = db.execute(
                    t_caseparticipantaccess.select().where(t_caseparticipantaccess.c.caseid == c.caseid)
                ).first()

                if access_row:
                    participant = db.query(Caseparticipant).filter_by(participantid=access_row.participantid).first()
                    if participant:
                        client_user = db.query(Users).filter_by(userid=participant.userid).first()
                        if client_user:
                            client_name = f"{client_user.firstname or ''} {client_user.lastname or ''}".strip()

                result.append({
                    'id': c.caseid,
                    'title': c.title,
                    'description': c.description,
                    'casetype': c.casetype,
                    'filingdate': c.filingdate.isoformat() if c.filingdate else None,
                    'status': c.status,
                    'clientname': client_name,
                    'courtname': court_name_str,
                    'judgeName': judge_name or 'N/A',
                    'prosecutorName': prosecutor_name,
                    'remandstatus': remand_status,
                    'decisionId': decision_data.get('decisionId', ''),
                    'decisiondate': decision_data.get('decisionDate', ''),
                    'decisionsummary': decision_data.get('decisionSummary', ''),
                    'verdict': decision_data.get('verdict', ''),
                    'history': history
                })

            return jsonify({'cases': result}), 200

        elif role == 'Judge':
            judge = db.query(Judge).filter_by(userid=userid).first()
            if not judge:
                return jsonify({'message': 'Judge profile not found'}), 404

            query = db.query(Cases).join(Cases.judge).filter(Judge.judgeid == judge.judgeid)
            cases = query.distinct().all()

            result = []
            for c in cases:
                court_names = [court.courtname for court in c.court if court.courtname]
                court_name_str = ', '.join(court_names)

                lawyer_names = []
                for lawyer in c.lawyer:
                    if lawyer.users:
                        full_name = f"{lawyer.users.firstname or ''} {lawyer.users.lastname or ''}".strip()
                        lawyer_names.append(full_name)
                lawyers_str = ' & '.join(lawyer_names)

                history = [
                    {
                        'date': h.actiondate.isoformat() if h.actiondate else None,
                        'event': h.actiontaken
                    }
                    for h in c.casehistory
                ]

                final_decision = None
                if c.finaldecision:
                    fd = c.finaldecision[0]
                    final_decision = {
                        'verdict': fd.verdict,
                        'summary': fd.decisionsummary,
                        'date': fd.decisiondate.isoformat() if fd.decisiondate else None
                    }

                evidence = [
                    {
                        'id': e.evidenceid,
                        'type': e.evidencetype,
                        'description': e.description,
                        'submittedDate': e.submitteddate.isoformat() if e.submitteddate else None,
                        'evidencePath': e.filepath
                    }
                    for e in c.evidence
                ]

                witness_links = db.query(Witnesscase).filter_by(caseid=c.caseid).all()
                witnesses = []
                for link in witness_links:
                    witness = db.query(Witnesses).filter_by(witnessid=link.witnessid).first()
                    if witness:
                        witnesses.append({
                            'id': witness.witnessid,
                            'firstName': witness.firstname,
                            'lastName': witness.lastname,
                            'cnic': witness.cnic,
                            'phone': witness.phone,
                            'email': witness.email,
                            'address': witness.address,
                            'pastHistory': witness.pasthistory
                        })

                result.append({
                    'id': c.caseid,
                    'title': c.title,
                    'description': c.description,
                    'caseType': c.casetype,
                    'filingDate': c.filingdate.isoformat() if c.filingdate else None,
                    'status': c.status,
                    'lawyers': lawyers_str,
                    'clientName': "",
                    'courtName': court_name_str,
                    'nextHearing': "N/A",
                    'remarks': "",
                    'finalDecision': final_decision,
                    'history': history,
                    'evidence': evidence,
                    'witnesses': witnesses
                })

            return jsonify({'cases': result}), 200

        elif role == 'CaseParticipant':
            participant = db.query(Caseparticipant).filter_by(userid=userid).first()
            if not participant:
                return jsonify({'message': 'CaseParticipant profile not found'}), 404

            access_rows = db.execute(
                t_caseparticipantaccess.select().filter_by(participantid=participant.participantid)
            ).fetchall()
            case_ids = [row[0] for row in access_rows]

            if not case_ids:
                return jsonify({'cases': []}), 200

            cases = db.query(Cases).filter(Cases.caseid.in_(case_ids)).distinct().all()
            result = []

            for c in cases:
                court_names = [court.courtname for court in c.court if court.courtname]
                court_name_str = ', '.join(court_names)

                lawyer_names = []
                for lawyer in c.lawyer:
                    if lawyer.users:
                        full_name = f"{lawyer.users.firstname or ''} {lawyer.users.lastname or ''}".strip()
                        lawyer_names.append(full_name)
                lawyers_str = ' & '.join(lawyer_names)

                history = [
                    {
                        'date': h.actiondate.isoformat() if h.actiondate else None,
                        'event': h.actiontaken
                    }
                    for h in c.casehistory
                ]

                final_decision = None
                if c.finaldecision:
                    fd = c.finaldecision[0]
                    final_decision = {
                        'verdict': fd.verdict,
                        'summary': fd.decisionsummary,
                        'date': fd.decisiondate.isoformat() if fd.decisiondate else None
                    }

                evidence = [
                    {
                        'id': e.evidenceid,
                        'type': e.evidencetype,
                        'description': e.description,
                        'submittedDate': e.submitteddate.isoformat() if e.submitteddate else None,
                        'evidencePath': e.filepath
                    }
                    for e in c.evidence
                ]

                witness_links = db.query(Witnesscase).filter_by(caseid=c.caseid).all()
                witnesses = []
                for link in witness_links:
                    witness = db.query(Witnesses).filter_by(witnessid=link.witnessid).first()
                    if witness:
                        witnesses.append({
                            'id': witness.witnessid,
                            'firstName': witness.firstname,
                            'lastName': witness.lastname,
                            'cnic': witness.cnic,
                            'phone': witness.phone,
                            'email': witness.email,
                            'address': witness.address,
                            'pastHistory': witness.pasthistory
                        })

                result.append({
                    'id': c.caseid,
                    'title': c.title,
                    'description': c.description,
                    'caseType': c.casetype,
                    'filingDate': c.filingdate.isoformat() if c.filingdate else None,
                    'status': c.status,
                    'lawyers': lawyers_str,
                    'clientName': "",
                    'courtName': court_name_str,
                    'nextHearing': "N/A",
                    'remarks': "",
                    'finalDecision': final_decision,
                    'history': history,
                    'evidence': evidence,
                    'witnesses': witnesses
                })

            return jsonify({'cases': result}), 200

        elif role == 'CourtRegistrar':
            court_registrar = db.query(Courtregistrar).filter_by(userid=userid).first()
            if not court_registrar:
                return jsonify({'message': 'CourtRegistrar not found'}), 404

            court_id = court_registrar.courtid

            client_user = aliased(Users)
            lawyer_user = aliased(Users)
            judge_user = aliased(Users)

            cases = (
                db.query(
                    Cases.caseid,
                    Cases.title,
                    Cases.description,
                    Cases.casetype,
                    Cases.filingdate,
                    Cases.status,
                    (client_user.firstname + ' ' + client_user.lastname).label('clientname'),
                    (lawyer_user.firstname + ' ' + lawyer_user.lastname).label('lawyername'),
                    Prosecutor.name.label('prosecutor'),
                    (judge_user.firstname + ' ' + judge_user.lastname).label('judgename'),
                )
                .join(t_courtaccess, t_courtaccess.c.caseid == Cases.caseid)
                .filter(t_courtaccess.c.courtid == court_id)
                .outerjoin(t_caseparticipantaccess, t_caseparticipantaccess.c.caseid == Cases.caseid)
                .outerjoin(Caseparticipant, Caseparticipant.participantid == t_caseparticipantaccess.c.participantid)
                .outerjoin(client_user, client_user.userid == Caseparticipant.userid)
                .outerjoin(t_caselawyeraccess, t_caselawyeraccess.c.caseid == Cases.caseid)
                .outerjoin(Lawyer, Lawyer.lawyerid == t_caselawyeraccess.c.lawyerid)
                .outerjoin(lawyer_user, lawyer_user.userid == Lawyer.userid)
                .outerjoin(t_judgeaccess, t_judgeaccess.c.caseid == Cases.caseid)
                .outerjoin(Judge, Judge.judgeid == t_judgeaccess.c.judgeid)
                .outerjoin(judge_user, judge_user.userid == Judge.userid)
                .outerjoin(t_prosecutorassign, t_prosecutorassign.c.caseid == Cases.caseid)
                .outerjoin(Prosecutor, Prosecutor.prosecutorid == t_prosecutorassign.c.prosecutorid)
                .distinct()
                .all()
            )

            result = [
                {
                    'caseid': c.caseid,
                    'title': c.title,
                    'description': c.description,
                    'casetype': c.casetype,
                    'filingdate': c.filingdate.isoformat() if c.filingdate else None,
                    'status': c.status,
                    'clientName': c.clientname,
                    'lawyername': c.lawyername,
                    'prosecutor': c.prosecutor,
                    'judgeName': c.judgename,
                }
                for c in cases
            ]

            return jsonify({'cases': result}), 200

        # Apply filters for non-judge roles
        if status:
            query = query.filter(Cases.status == status)
        if casetype:
            query = query.filter(Cases.casetype == casetype)
        if title:
            query = query.filter(Cases.title.ilike(f"%{title}%"))

        cases = query.distinct().all()
        result = [
            {
                'caseid': c.caseid,
                'title': c.title,
                'description': c.description,
                'casetype': c.casetype,
                'filingdate': c.filingdate.isoformat() if c.filingdate else None,
                'status': c.status,
            }
            for c in cases
        ]

        return jsonify({'cases': result}), 200

    except Exception as e:
        logging.error("Error in get_cases:", exc_info=True)
        return jsonify({'message': str(e)}), 500

    finally:
        db.close()


from sqlalchemy import func

@app.route('/api/hearings', methods=['GET'])
@login_required
def get_hearings_role():
    db = SessionLocal()
    try:
        userid = current_user.userid
        role = current_user.role

        if role == 'CourtRegistrar':
            # Your existing CourtRegistrar logic (unchanged)
            court_registrar = db.query(Courtregistrar).filter_by(userid=userid).first()
            if not court_registrar:
                return jsonify({'message': 'CourtRegistrar not found'}), 404

            court_id = court_registrar.courtid

            court_access_cases = db.execute(
                t_courtaccess.select().filter_by(courtid=court_id)
            ).fetchall()

            if not court_access_cases:
                return jsonify({'message': 'No cases found for this court.'}), 404

            case_ids = [row[0] for row in court_access_cases]

            query = (
                db.query(
                    Hearings.hearingid,
                    Hearings.hearingdate,
                    Hearings.hearingtime,
                    Cases.title.label('casename'),
                    Users.firstname,
                    Users.lastname,
                    Hearings.venue.label('courtroomno')
                )
                .join(Cases, Hearings.caseid == Cases.caseid)
                .outerjoin(Judge, Hearings.judgeid == Judge.judgeid)
                .outerjoin(Users, Judge.userid == Users.userid)
                .filter(Hearings.caseid.in_(case_ids))
                .order_by(Hearings.hearingdate.desc(), Hearings.hearingtime.asc())
            )

            results = query.all()

            output = []
            for hearingid, hearingdate, hearingtime, casename, firstname, lastname, courtroomno in results:
                output.append({
                    'hearingid': hearingid,
                    'hearingdate': hearingdate.isoformat(),
                    'hearingtime': hearingtime.strftime("%H:%M") if hearingtime else None,
                    'casename': casename,
                    'courtroomno': courtroomno if courtroomno else "N/A",
                    'judgename': f"{firstname} {lastname}" if firstname and lastname else "Unassigned"
                })

            return jsonify({'hearings': output}), 200

        elif role == 'Judge':
            # New logic for Judge: join hearings -> cases -> courtaccess -> court to get courtname
            judge = db.query(Judge).filter_by(userid=userid).first()
            if not judge:
                return jsonify({'message': 'Judge profile not found'}), 404

            query = (
                db.query(
                    Hearings.hearingid,
                    Cases.title.label('casetitle'),
                    Court.courtname,
                    Hearings.hearingdate,
                    Hearings.hearingtime,
                    Hearings.remarks,
                )
                .join(Hearings, Hearings.caseid == Cases.caseid)
                .join(t_courtaccess, t_courtaccess.c.caseid == Cases.caseid)
                .join(Court, Court.courtid == t_courtaccess.c.courtid)
                .filter(Hearings.judgeid == judge.judgeid)
                .order_by(Hearings.hearingdate.desc(), Hearings.hearingtime.asc())
            )

            results = query.all()

            output = []
            for hearingid,casetitle, courtname, hearingdate, hearingtime, remarks in results:
                output.append({
                    'id':hearingid,
                    'casetitle': casetitle,
                    'courtname': courtname,
                    'hearingdate': hearingdate.isoformat(),
                    'hearingtime': hearingtime.strftime("%H:%M") if hearingtime else None,
                    'remarks': remarks or ''
                })

            return jsonify({'hearings': output}), 200

        else:
            # Your existing logic for other roles (Lawyer, CaseParticipant, etc.)
            query = db.query(Hearings)

            if role == 'Lawyer':
                lawyer = db.query(Lawyer).filter_by(userid=userid).first()
                if not lawyer:
                    return jsonify({'message': 'Lawyer profile not found'}), 404
                query = query.join(Cases).join(Cases.lawyer).filter(Lawyer.lawyerid == lawyer.lawyerid)

            elif role == 'CaseParticipant':
                participant = db.query(Caseparticipant).filter_by(userid=userid).first()
                if not participant:
                    return jsonify({'message': 'CaseParticipant profile not found'}), 404
                query = query.join(Cases).join(Cases.caseparticipant).filter(Caseparticipant.participantid == participant.participantid)

            else:
                return jsonify({'message': f'Role {role} not supported'}), 403

            hearings = query.distinct().all()

            result = [
                {
                    'hearingid': h.hearingid,
                    'hearingdate': h.hearingdate.isoformat(),
                    'hearingtime': h.hearingtime.strftime("%H:%M") if h.hearingtime else None,
                    'courtroomid': (
                        h.venue.split('#')[-1].strip()
                        if h.venue and '#' in h.venue else 'N/A'
                    )
                }
                for h in hearings
            ]

            return jsonify({'hearings': result}), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 500

    finally:
        db.close()


@app.route('/api/hearings/addvenue', methods=['PUT'])
@login_required
def add_venue_to_hearing():
    conn = get_pg_connection()
    cursor = conn.cursor()
    try:
        data = request.get_json()
        hearing_id = data.get('hearingid')
        venue = data.get('venue')

        if not hearing_id or not venue:
            return jsonify({'message': 'Missing hearingid or venue'}), 400

        # Check if hearing exists
        cursor.execute("SELECT hearingid FROM hearings WHERE hearingid = %s", (hearing_id,))
        hearing = cursor.fetchone()
        if not hearing:
            return jsonify({'message': 'Hearing not found'}), 404

        # Update venue
        cursor.execute("UPDATE hearings SET venue = %s WHERE hearingid = %s", (venue, hearing_id))
        conn.commit()

        return jsonify({'message': 'Venue updated successfully', 'hearingid': hearing_id, 'venue': venue}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/api/casebyid', methods=['GET'])
@login_required
def get_cases_by_id():
    db = SessionLocal()
    try: 
        user_role = current_user.role.lower()  # 'lawyer', 'client', or 'judge'
        user_id = current_user.userid

        query = db.query(Cases)

        if user_role == 'lawyer':
            query = query.filter(Cases.lawyerid == user_id)
        elif user_role == 'client':
            query = query.filter(Cases.clientid == user_id)
        elif user_role == 'judge':
            query = query.filter(Cases.judgeid == user_id)
        else:
            return jsonify({'message': 'Invalid user role'}), 400

        cases = query.all()

        result = [
            {
                'caseid': c.caseid,
                'title': c.title,
                'description': c.description,
                'casetype': c.casetype,
                'filingdate': c.filingdate.isoformat() if c.filingdate else None,
                'status': c.status,
                'lawyerid': c.lawyerid,
                'clientid': c.clientid,
                'judgeid': c.judgeid,
            }
            for c in cases
        ]

        return jsonify({'cases': result}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()



@app.route('/api/cases/<int:case_id>', methods=['PUT'])
@login_required
def update_case(case_id):
    db = SessionLocal()
    try:
        data = request.get_json()
        case = db.query(Cases).get(case_id)

        if not case:
            return jsonify({'message': 'Case not found'}), 404

        case.title = data.get('title', case.title)
        case.description = data.get('description', case.description)
        case.casetype = data.get('casetype', case.casetype)
        case.status = data.get('status', case.status)

        db.commit()
        return jsonify({'message': 'Case updated successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@app.route('/api/cases/<int:case_id>', methods=['DELETE'])
@login_required
def delete_case(case_id):
    db = SessionLocal()
    try:
        case = db.query(Cases).get(case_id)

        if not case:
            return jsonify({'message': 'Case not found'}), 404

        db.delete(case)
        db.commit()
        return jsonify({'message': 'Case deleted successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
@app.route('/api/cases/<int:case_id>/assign', methods=['POST'])
@login_required
def assign_case(case_id):
    db = SessionLocal()
    try:
        data = request.get_json()
        assignee_id = data.get('assignee_id')
        role = data.get('role')  # 'lawyer' or 'judge'

        case = db.query(Cases).get(case_id)
        if not case:
            return jsonify({'message': 'Case not found'}), 404

        if role == 'lawyer':
            lawyer = db.query(Lawyer).get(assignee_id)
            if not lawyer:
                return jsonify({'message': 'Lawyer not found'}), 404
            case.lawyer.append(lawyer)
        elif role == 'judge':
            judge = db.query(Judge).get(assignee_id)
            if not judge:
                return jsonify({'message': 'Judge not found'}), 404
            case.judge.append(judge)
        else:
            return jsonify({'message': 'Invalid role'}), 400

        db.commit()
        return jsonify({'message': 'Case assigned successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
@app.route('/api/cases/<int:case_id>/history', methods=['GET'])
@login_required
def get_case_history(case_id):
    db = SessionLocal()
    try:
        history = db.query(Casehistory).filter_by(caseid=case_id).all()
        result = []

        for h in history:
            case = db.query(Cases).filter_by(caseid=case_id).first()

            # Fetch related judge (first one for simplicity)
            judge = case.judge[0].users if case.judge else None
            lawyer = case.lawyer[0].users if case.lawyer else None
            client = case.caseparticipant[0].users if case.caseparticipant else None

            result.append({
                'caseName': case.title,
                'judgeName': f"{judge.firstname} {judge.lastname}" if judge else "N/A",
                'lawyerName': f"{lawyer.firstname} {lawyer.lastname}" if lawyer else "N/A",
                'clientName': f"{client.firstname} {client.lastname}" if client else "N/A",
                'remarks': h.remarks,
                'date': h.actiondate.isoformat() if h.actiondate else None,
                'event': h.actiontaken,
                'status': case.status  # or h.status if it exists per entry
            })

        return jsonify({'history': result}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

        
# @app.route('/api/cases/<int:case_id>/history', methods=['GET'])
# @login_required
# def get_case_history(case_id):
#     db = SessionLocal()
#     try:
#         history = db.query(Casehistory).filter_by(caseid=case_id).all()
#         result = [
#             {
#                 'actiondate': h.actiondate.isoformat(),
#                 'actiontaken': h.actiontaken,
#                 'remarks': h.remarks
#             }
#             for h in history
#         ]
#         return jsonify({'history': result}), 200
#     except Exception as e:
#         return jsonify({'message': str(e)}), 500
#     finally:
#         db.close()
 
        

@app.route('/api/appeals', methods=['POST'])
@login_required
def create_appeal():
    conn = None
    try:
        data = request.get_json()

        casename = data.get('casename')
        casetype = data.get('casetype')
        courtname = data.get('court')

        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Look up the caseid
        cur.execute("""
            SELECT caseid FROM cases
            WHERE title = %s AND casetype = %s
            LIMIT 1
        """, (casename, casetype))
        case = cur.fetchone()

        if not case:
            return jsonify({'message': 'Case not found with the given details'}), 404

        # Check if court exists
        cur.execute("""
            SELECT courtid FROM court WHERE courtname = %s LIMIT 1
        """, (courtname,))
        court = cur.fetchone()

        if not court:
            return jsonify({'message': 'Court not found'}), 404

        # Insert the appeal with current date and appealstatus
        cur.execute("""
            INSERT INTO appeals (appealdate, caseid)
            VALUES (%s, %s)
            RETURNING appealid
        """, (datetime.datetime.now(), case['caseid']))

        appeal_id = cur.fetchone()['appealid']
        conn.commit()
        cur.close()

        return jsonify({'message': 'Appeal created successfully', 'appealid': appeal_id}), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        if conn:
            conn.close()
            
@app.route('/api/appeals', methods=['GET'])
@login_required
def get_appeals():
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        query = """
        SELECT 
            a.appealid,
            a.appealdate,
            a.appealstatus,
            a.decisiondate,
            a.decision,
            c.title AS casename,
            ct.courtname,

            -- Lawyer name
            u1.firstname || ' ' || u1.lastname AS lawyername,

            -- Case participant name
            u2.firstname || ' ' || u2.lastname AS caseparticipantname

        FROM appeals a
        JOIN cases c ON c.caseid = a.caseid
        JOIN courtaccess ca ON ca.caseid = c.caseid
        JOIN court ct ON ct.courtid = ca.courtid

        LEFT JOIN caselawyeraccess cla ON cla.caseid = c.caseid
        LEFT JOIN lawyer l ON l.lawyerid = cla.lawyerid
        LEFT JOIN users u1 ON u1.userid = l.userid

        LEFT JOIN caseparticipantaccess cpa ON cpa.caseid = c.caseid
        LEFT JOIN caseparticipant cp ON cp.participantid = cpa.participantid
        LEFT JOIN users u2 ON u2.userid = cp.userid;
        """

        cur.execute(query)
        rows = cur.fetchall()

        result = [
            {
                'appealid' : row[0],
                'appealdate': row[1],
                'status': row[2],
                'decisiondate': row[3],
                'decision': row[4],
                'casename': row[5],
                'courtname': row[6],
                'lawyername': row[7],
                'clientname': row[8]
            }
            for row in rows
        ]

        cur.close()
        conn.close()
        return jsonify({'appeals': result}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({'message': str(e)}), 500

@app.route('/api/appealdecision', methods=['PUT'])
def update_appeal_decision():
    conn = None
    cur = None
    try:
        appeal_id = request.args.get('appealId')
        if not appeal_id:
            return jsonify({'error': 'appealId is required as a query parameter'}), 400

        data = request.get_json()
        appeal_status = data.get('appealStatus')
        decision_date = data.get('decisionDate')
        decision = data.get('decision')

        if decision_date:
            try:
                decision_date = datetime.datetime.strptime(decision_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid decisionDate format. Use YYYY-MM-DD'}), 400

        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        query = """
            UPDATE appeals
            SET appealstatus = %s,
                decisiondate = %s,
                decision = %s
            WHERE appealid = %s
        """
        cur.execute(query, (appeal_status, decision_date, decision, appeal_id))
        conn.commit()

        if cur.rowcount == 0:
            return jsonify({'message': 'Appeal not found'}), 404

        return jsonify({'message': 'Appeal decision updated successfully'}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'Failed to update appeal decision'}), 500

    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

@app.route('/api/lawyerappeals', methods=['GET'])
@login_required
def get_lawyerappeals():
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        # Step 1: Get lawyerid using current_user.userid
        cur.execute("SELECT lawyerid FROM lawyer WHERE userid = %s;", (current_user.userid,))
        lawyer_row = cur.fetchone()
        if not lawyer_row:
            return jsonify({'message': 'Lawyer profile not found'}), 404

        lawyerid = lawyer_row[0]

        # Step 2: Get appeals for cases accessible to this lawyer
        query = """
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
        );
        """
        cur.execute(query, (lawyerid,))
        rows = cur.fetchall()

        result = [
            {
                'appealdate': row[0],
                'status': row[1],
                'decisiondate': row[2],
                'decision': row[3],
                'casename': row[4],
                'courtname': row[5]
            }
            for row in rows
        ]

        cur.close()
        conn.close()
        return jsonify({'appeals': result}), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/api/hearings/remarks', methods=['PUT'])
@login_required
def update_hearing_remarks():
    try:
        hearing_id = request.args.get('hearingid')
        if not hearing_id:
            return jsonify({'error': 'hearingid query parameter is required'}), 400

        data = request.get_json()
        remarks = data.get('remarks')
        if remarks is None:
            return jsonify({'error': 'remarks field is required in JSON body'}), 400

        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute(
            "UPDATE hearings SET remarks = %s WHERE hearingid = %s",
            (remarks, hearing_id)
        )

        if cur.rowcount == 0:
            return jsonify({'error': 'Hearing not found'}), 404

        conn.commit()
        return jsonify({'message': 'Remarks updated successfully'}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        print("Error updating remarks:", e)
        return jsonify({'error': str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route('/api/hearings', methods=['POST'])
@login_required
def schedule_hearing():
    try:
        data = request.get_json()

        casetitle = data.get('casetitle')
        courtname = data.get('courtname')
        hearingdate = data.get('hearingdate')
        hearingtime = data.get('hearingtime')
        remarks = data.get('remarks', None)  # Optional

        if not all([casetitle, courtname, hearingdate, hearingtime]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Establish DB connection
        conn = get_pg_connection()
        cur = conn.cursor()

        # Get judgeid from current user
        cur.execute("SELECT judgeid FROM judge WHERE userid = %s", (current_user.userid,))
        judge_row = cur.fetchone()
        if not judge_row:
            return jsonify({'error': 'Judge profile not found'}), 404
        judgeid = judge_row[0]

        # Get caseid from case title
        cur.execute("SELECT caseid FROM cases WHERE title = %s LIMIT 1", (casetitle,))
        case_row = cur.fetchone()
        if not case_row:
            return jsonify({'error': 'Case not found'}), 404
        caseid = case_row[0]

        # Insert hearing
        cur.execute("""
            INSERT INTO hearings (caseid, judgeid, hearingdate, hearingtime,remarks)
            VALUES (%s, %s, %s, %s, %s)
        """, (caseid, judgeid, hearingdate, hearingtime, remarks))

        conn.commit()
        return jsonify({'message': 'Hearing scheduled successfully'}), 201

    except Exception as e:
        print("Error scheduling hearing:", e)
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

        
@app.route('/api/hearings', methods=['GET'])
@login_required
def get_hearings():
    db = SessionLocal()
    try:
        userid = current_user.userid
        role = current_user.role

        query = db.query(Hearings)

        if role == 'Lawyer':
            lawyer = db.query(Lawyer).filter_by(userid=userid).first()
            if not lawyer:
                return jsonify({'message': 'Lawyer profile not found'}), 404
            query = query.join(Cases).join(Cases.lawyer).filter(Lawyer.lawyerid == lawyer.lawyerid)

        elif role == 'Judge':
            judge = db.query(Judge).filter_by(userid=userid).first()
            if not judge:
                return jsonify({'message': 'Judge profile not found'}), 404
            query = query.join(Cases).join(Cases.judge).filter(Judge.judgeid == judge.judgeid)

        elif role == 'CaseParticipant':
            participant = db.query(Caseparticipant).filter_by(userid=userid).first()
            if not participant:
                return jsonify({'message': 'CaseParticipant profile not found'}), 404
            query = query.join(Cases).join(Cases.caseparticipant).filter(Caseparticipant.participantid == participant.participantid)

        elif role == 'Admin':
            pass  # show all hearings

        hearings = query.distinct().all()

        result = [
            {
                'hearingid': h.hearingid,
                'hearingdate': h.hearingdate.isoformat(),
                'hearingtime': h.hearingtime.strftime("%H:%M") if h.hearingtime else None,
                'courtroomid': getattr(h, 'courtroomid', 'N/A')  # Optional
            }
            for h in hearings
        ]

        return jsonify({'hearings': result}), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 500

    finally:
        db.close()


@app.route('/api/bails', methods=['POST'])
@login_required
def create_bail():
    conn = get_pg_connection()
    cursor = conn.cursor()

    try:
        data = request.get_json()
        casename = data.get('casename')
        bail_date = data.get('bail_date') or datetime.datetime.date.today()
        suretyid = data.get('suretyid')

        if not casename:
            return jsonify({'message': 'Case name is required'}), 400

        # Find case ID based on case name
        cursor.execute("SELECT caseid FROM cases WHERE title = %s", (casename,))
        result = cursor.fetchone()

        if not result:
            return jsonify({'message': 'Case not found'}), 404

        case_id = result[0]

        # Insert bail record
        cursor.execute("""
            INSERT INTO bail (caseid, baildate,bailstatus,suretyid)
            VALUES (%s, %s,%s,%s)
            RETURNING bailid
        """, (case_id, bail_date, 'Pending',suretyid))

        bail_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({'message': 'Bail created successfully', 'bail_id': bail_id}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/api/bails/<int:case_id>', methods=['GET'])
@login_required
def get_bail(bail_id):
    db = SessionLocal()
    try:
        bail = db.query(Bail).get(bail_id)
        if not bail:
            return jsonify({'message': 'Bail not found'}), 404

        return jsonify({
            'bail_id': bail.bailid,
            'case_id': bail.caseid,
            'amount': float(bail.amount),
            'bail_date': bail.baildate.isoformat(),
            'status': bail.status
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
@app.route('/api/bails', methods=['GET'])
@login_required
def get_bails_for_lawyer():
    db = SessionLocal()
    try:
        if current_user.role != 'Lawyer':
            return jsonify({'message': 'Access denied'}), 403

        # Get the lawyer profile based on the current user's ID
        lawyer = db.query(Lawyer).filter_by(userid=current_user.userid).first()
        if not lawyer:
            return jsonify({'message': 'Lawyer profile not found'}), 404

        # Get all bails linked to this lawyer’s cases
        bails = (
            db.query(Bail)
            .join(Cases, Bail.caseid == Cases.caseid)
            .join(Cases.lawyer)
            .filter(Lawyer.lawyerid == lawyer.lawyerid)
            .all()
        )

        result = [
            {
                'bailid': b.bailid,
                'caseid': b.caseid,
                'bailstatus': b.bailstatus,
                'bailamount': float(b.bailamount) if b.bailamount else None,
                'baildate': b.baildate.isoformat() if b.baildate else None,
                'remarks': b.remarks,
                'bailcondition': b.bailcondition
            }
            for b in bails
        ]
        return jsonify({'bails': result}), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()


@app.route('/api/cases/<int:case_id>/bails', methods=['GET'])
@login_required
def get_bails_for_case(case_id):
    db = SessionLocal()
    try:
        bails = db.query(Bail).filter_by(caseid=case_id).all()
        result = [
            {
                'bail_id': b.bailid,
                'amount': float(b.amount),
                'bail_date': b.baildate.isoformat(),
                'status': b.status
            }
            for b in bails
        ]
        return jsonify({'bails': result}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
@app.route('/api/bails/<int:bail_id>', methods=['PUT'])
@login_required
# @log_action(action_type = "UPDATE", entity_type = "Bails")
def update_bail(bail_id):
    db = SessionLocal()
    try:
        data = request.get_json()
        bail = db.query(Bail).get(bail_id)

        if not bail:
            return jsonify({'message': 'Bail not found'}), 404

        bail.amount = data.get('amount', bail.amount)
        bail.status = data.get('status', bail.status)
        bail.baildate = data.get('bail_date', bail.baildate)

        db.commit()
        return jsonify({'message': 'Bail updated successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@app.route('/api/evidence', methods=['GET'])
def get_evidence():
    try:
        # Step 0: Connect to the database
        conn = get_pg_connection()
        cursor = conn.cursor()

        # Step 1: Get current user ID
        userid = current_user.userid  # Ensure this is retrieved securely

        # Step 2: Get court_id from courtregistrar
        cursor.execute("SELECT courtid FROM courtregistrar WHERE userid = %s", (userid,))
        registrar = cursor.fetchone()
        if not registrar:
            return jsonify({'message': 'CourtRegistrar not found'}), 404

        court_id = registrar[0]

        # Step 3: Get accessible case IDs for this court
        cursor.execute("SELECT caseid FROM courtaccess WHERE courtid = %s", (court_id,))
        case_rows = cursor.fetchall()
        if not case_rows:
            return jsonify({"error": "No cases found for this court"}), 404

        case_ids = [row[0] for row in case_rows]

        # Step 4: Fetch evidence along with case title and caseid
        format_strings = ','.join(['%s'] * len(case_ids))
        evidence_query = f"""
            SELECT e.evidenceid, e.evidencetype, e.description, e.submitteddate, e.filepath,
                   c.title, c.caseid
            FROM evidence e
            JOIN cases c ON e.caseid = c.caseid
            WHERE e.caseid IN ({format_strings})
        """
        cursor.execute(evidence_query, case_ids)
        evidence_rows = cursor.fetchall()

        result = []
        for row in evidence_rows:
            evidenceid, evidencetype, description, submitteddate, filepath, casetitle, caseid = row

            # Step 5: Fetch lawyerid from caselawyeraccess
            cursor.execute("SELECT lawyerid FROM caselawyeraccess WHERE caseid = %s", (caseid,))
            lawyer_row = cursor.fetchone()
            lawyername = None
            if lawyer_row:
                lawyerid = lawyer_row[0]

                # Step 6: Get userid from lawyer table
                cursor.execute("SELECT userid FROM lawyer WHERE lawyerid = %s", (lawyerid,))
                lawyer_user_row = cursor.fetchone()
                if lawyer_user_row:
                    lawyer_userid = lawyer_user_row[0]

                    # Step 7: Get name from users table
                    cursor.execute("SELECT firstname, lastname FROM users WHERE userid = %s", (lawyer_userid,))
                    name_row = cursor.fetchone()
                    if name_row:
                        lawyername = f"{name_row[0]} {name_row[1]}"

            # Add evidence to result
            result.append({
                "id": evidenceid,
                "evidenceType": evidencetype,
                "description": description,
                "submissionDate": submitteddate.strftime('%Y-%m-%d') if submitteddate else None,
                "caseName": casetitle,
                "lawyerName": lawyername,
                "file": filepath
            })

        return jsonify({"evidence": result})

    except Exception as ex:
        print("Error:", ex)
        print("Full traceback:", traceback.format_exc())
        return jsonify({"error": "Failed to fetch evidence"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


        
@app.route('/api/bails/<int:bail_id>', methods=['DELETE'])
@login_required
# @log_action(action_type = "DELETE", entity_type = "Bails")
def delete_bail(bail_id):
    db = SessionLocal()
    try:
        bail = db.query(Bail).get(bail_id)
        if not bail:
            return jsonify({'message': 'Bail not found'}), 404

        db.delete(bail)
        db.commit()
        return jsonify({'message': 'Bail deleted successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@app.route('/api/surety', methods=['POST'])
@login_required
def create_surety():
    conn = get_pg_connection()
    cursor = conn.cursor()

    try:
        data = request.get_json()

        firstname = data.get('firstname')
        lastname = data.get('lastname')
        cnic = data.get('cnic')
        phone = data.get('phone')
        email = data.get('email')
        address = data.get('address')
        past_history = data.get('past_history')
        casename = data.get('casename')

        if not all([firstname, lastname, cnic, phone, email, address, casename]):
            return jsonify({'message': 'Missing required fields'}), 400

        # Step 1: Get case ID from casename
        cursor.execute("SELECT caseid FROM cases WHERE casename = %s", (casename,))
        case_result = cursor.fetchone()

        if not case_result:
            return jsonify({'message': 'Case not found'}), 404

        case_id = case_result[0]

        # Step 2: Get bail ID for the given case
        cursor.execute("SELECT bailid FROM bail WHERE caseid = %s", (case_id,))
        bail_result = cursor.fetchone()

        if not bail_result:
            return jsonify({'message': 'Bail not found for this case'}), 404

        bail_id = bail_result[0]

        # Step 3: Insert new surety
        cursor.execute("""
            INSERT INTO surety (firstname, lastname, cnic, phone, email, address, past_history)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING suretyid
        """, (firstname, lastname, cnic, phone, email, address, past_history))

        surety_id = cursor.fetchone()[0]

        # Step 4: Update bail with suretyid
        cursor.execute("""
            UPDATE bail
            SET suretyid = %s
            WHERE bailid = %s
        """, (surety_id, bail_id))

        conn.commit()

        return jsonify({'message': 'Surety created and linked to bail successfully'}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/api/surety/<int:surety_id>', methods=['GET'])
@login_required
def get_surety(surety_id):
    db = SessionLocal()
    try:
        surety = db.query(Surety).get(surety_id)
        if not surety:
            return jsonify({'message': 'Surety not found'}), 404

        return jsonify({
            'surety_id': surety.suretyid,
            'name': surety.name,
            'cnic': surety.cnic,
            'address': surety.address,
            'relationship': surety.relationship,
            'bailid': surety.bailid
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@app.route('/api/surety/<int:surety_id>', methods=['PUT'])
@login_required
# @log_action(action_type = "UPDATE", entity_type = "Surety")
def update_surety(surety_id):
    db = SessionLocal()
    try:
        data = request.get_json()
        surety = db.query(Surety).get(surety_id)

        if not surety:
            return jsonify({'message': 'Surety not found'}), 404

        surety.name = data.get('name', surety.name)
        surety.cnic = data.get('cnic', surety.cnic)
        surety.address = data.get('address', surety.address)
        surety.relationship = data.get('relationship', surety.relationship)

        db.commit()
        return jsonify({'message': 'Surety updated successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
@app.route('/api/surety/from-lawyer', methods=['GET'])
@login_required
def get_surety_by_lawyer():
    db = SessionLocal()
    try:
        if current_user.role != 'Lawyer':
            return jsonify({'message': 'Only lawyers can access this resource'}), 403

        # Get the lawyer object
        lawyer = db.query(Lawyer).filter_by(userid=current_user.userid).first()
        if not lawyer:
            return jsonify({'message': 'Lawyer not found'}), 404

        # Join Bail → Cases → caselawyeraccess manually
        bail = (
            db.query(Bail)
            .join(Cases, Bail.caseid == Cases.caseid)
            .join(t_caselawyeraccess, t_caselawyeraccess.c.caseid == Cases.caseid)
            .filter(t_caselawyeraccess.c.lawyerid == lawyer.lawyerid)
            .first()
        )

        if not bail:
            return jsonify({'message': 'No bail found for this lawyer'}), 404

        surety = bail.surety
        if not surety:
            return jsonify({'message': 'Surety not found for the bail'}), 404

        # 🧠 Query the Cases table directly to get the case title
        case = db.query(Cases).filter_by(caseid=bail.caseid).first()
        case_title = case.title if case else 'Unknown'

        return jsonify({
            'suretyid': surety.suretyid,
            'firstname': surety.firstname,
            'lastname': surety.lastname,
            'cnic': surety.cnic,
            'phone': surety.phone,
            'email': surety.email,
            'address': surety.address,
            'pasthistory': surety.pasthistory,
            'casename': case_title
        }), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()


@app.route('/api/surety/<int:surety_id>', methods=['DELETE'])
@login_required
def delete_surety(surety_id):
    db = SessionLocal()
    try:
        surety = db.query(Surety).get(surety_id)
        if not surety:
            return jsonify({'message': 'Surety not found'}), 404

        db.delete(surety)
        db.commit()
        return jsonify({'message': 'Surety deleted successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

        

@app.route('/api/cases/<int:case_id>/history', methods=['POST'])
@login_required
def add_case_history(case_id):
    db = SessionLocal()
    try:
        data = request.get_json()
        action_taken = data.get('actiontaken')
        remarks = data.get('remarks')

        if not action_taken:
            return jsonify({'message': 'Action taken is required'}), 400

        # Check if the case exists
        case = db.query(Cases).get(case_id)
        if not case:
            return jsonify({'message': 'Case not found'}), 404

        # Add a new history entry
        new_history = Casehistory(
            caseid=case_id,
            actiondate=datetime.date.today(),
            actiontaken=action_taken,
            remarks=remarks
        )
        db.add(new_history)
        db.commit()

        return jsonify({'message': 'Case history added successfully'}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
@app.route('/api/cases/history/<int:history_id>', methods=['PUT'])
@login_required
def update_case_history(history_id):
    db = SessionLocal()
    try:
        data = request.get_json()
        history = db.query(Casehistory).get(history_id)

        if not history:
            return jsonify({'message': 'History entry not found'}), 404

        history.actiontaken = data.get('actiontaken', history.actiontaken)
        history.remarks = data.get('remarks', history.remarks)
        history.updatedat = datetime.datetime.utcnow()

        db.commit()
        return jsonify({'message': 'Case history updated successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
@app.route('/api/cases/history/<int:history_id>', methods=['DELETE'])
@login_required
def delete_case_history(history_id):
    db = SessionLocal()
    try:
        history = db.query(Casehistory).get(history_id)

        if not history:
            return jsonify({'message': 'History entry not found'}), 404

        db.delete(history)
        db.commit()
        return jsonify({'message': 'Case history deleted successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        

@app.route('/api/cases/<int:case_id>/evidence', methods=['GET'])
@login_required
def get_evidence_for_case(case_id):
    db = SessionLocal()
    try:
        evidence = db.query(Evidence).filter_by(caseid=case_id).all()
        result = [
            {
                'evidence_id': e.evidenceid,
                'evidencetype': e.evidencetype,
                'description': e.description,
                'filepath': e.filepath,
                'submitteddate': e.submitteddate.isoformat()
            }
            for e in evidence
        ]
        return jsonify({'evidence': result}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
        

@app.route('/api/lawyer/evidence', methods=['GET'])
@login_required
def get_evidence_for_logged_in_lawyer():
    db = SessionLocal()
    try:
        user = db.query(Users).filter_by(userid=current_user.userid).first()

        if not user or user.role != 'Lawyer':
            return jsonify({'message': 'Access denied: User is not a lawyer'}), 403

        
        lawyer = db.query(Lawyer).filter_by(userid=user.userid).first()
        if not lawyer:
            return jsonify({'message': 'Lawyer profile not found'}), 404

        
        case_ids = db.query(t_caselawyeraccess.c.caseid).filter(
            t_caselawyeraccess.c.lawyerid == lawyer.lawyerid
        ).all()
        case_ids = [cid[0] for cid in case_ids]

        if not case_ids:
            return jsonify({'message': 'No cases assigned to this lawyer'}), 404

        # 4. Get evidence for those cases
        evidence_entries = db.query(Evidence).filter(Evidence.caseid.in_(case_ids)).all()

        result = [
            {
                'evidence_id': e.evidenceid,
                'case_id': e.caseid,
                'evidencetype': e.evidencetype,
                'description': e.description,
                'filepath': e.filepath,
                'submitteddate': e.submitteddate.isoformat() if e.submitteddate else None
            }
            for e in evidence_entries
        ]

        return jsonify({'evidence': result}), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@app.route('/api/evidence/<int:evidence_id>', methods=['PUT'])
@login_required
# @log_action(action_type = "UPDATE", entity_type = "Evidence")
def update_evidence(evidence_id):
    db = SessionLocal()
    try:
        data = request.get_json()
        evidence = db.query(Evidence).get(evidence_id)

        if not evidence:
            return jsonify({'message': 'Evidence not found'}), 404

        evidence.evidencetype = data.get('evidencetype', evidence.evidencetype)
        evidence.description = data.get('description', evidence.description)
        evidence.filepath = data.get('filepath', evidence.filepath)
        evidence.submitteddate = data.get('submitteddate', evidence.submitteddate)

        db.commit()
        return jsonify({'message': 'Evidence updated successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
@app.route('/api/evidence', methods=['POST'])
def add_evidence():
    try:
        data = request.get_json()

        evidencetype = data.get('evidencetype')
        description = data.get('description')
        submissiondate = data.get('submissiondate')  # e.g. '2024-05-10'
        casename = data.get('casename')

        if not all([evidencetype, description, submissiondate, casename]):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_pg_connection()
        cur = conn.cursor()

        # Step 1: Find caseid from casename
        cur.execute("SELECT caseid FROM cases WHERE title = %s", (casename,))
        case_result = cur.fetchone()

        if not case_result:
            return jsonify({'error': 'Case not found'}), 404

        caseid = case_result[0]

        # Step 2: Insert evidence
        cur.execute("""
            INSERT INTO evidence (evidencetype, description, submitteddate, caseid)
            VALUES (%s, %s, %s, %s)
        """, (
            evidencetype,
            description,
            datetime.datetime.strptime(submissiondate, '%Y-%m-%d'),  # Format check
            caseid
        ))

        conn.commit()

        return jsonify({'message': 'Evidence added successfully'}), 201

    except Exception as e:
        print("Error:", e)
        print(traceback.format_exc())
        return jsonify({'error': 'Failed to add evidence'}), 500

    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()


@app.route('/api/evidence/<int:evidence_id>', methods=['DELETE'])
@login_required
# @log_action(action_type = "DELETE", entity_type = "Evidence")
def delete_evidence(evidence_id):
    db = SessionLocal()
    try:
        evidence = db.query(Evidence).get(evidence_id)
        if not evidence:
            return jsonify({'message': 'Evidence not found'}), 404

        db.delete(evidence)
        db.commit()
        return jsonify({'message': 'Evidence deleted successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
#Witness API
@app.route('/api/cases/<int:case_id>/witnesses', methods=['POST'])
@login_required
# @log_action(action_type = "CREATE", entity_type = "Witnesses")
def add_witness(case_id):
    db = SessionLocal()
    try:
        data = request.get_json()
        firstname = data.get('firstname')
        lastname = data.get('lastname')
        cnic = data.get('cnic')
        phone = data.get('phone')
        email = data.get('email')
        address = data.get('address')
        statement = data.get('statement')
        statementdate = data.get('statementdate') or datetime.date.today()

        if not firstname or not lastname:
            return jsonify({'message': 'First name and last name are required'}), 400

        # Check if the case exists
        case = db.query(Cases).get(case_id)
        if not case:
            return jsonify({'message': 'Case not found'}), 404

        # Add witness
        new_witness = Witnesses(
            firstname=firstname,
            lastname=lastname,
            cnic=cnic,
            phone=phone,
            email=email,
            address=address,
            pasthistory=statement
        )
        db.add(new_witness)
        db.flush()

        # Link witness to the case
        witness_case = Witnesscase(
            caseid=case_id,
            witnessid=new_witness.witnessid,
            statement=statement,
            statementdate=statementdate
        )
        db.add(witness_case)
        db.commit()

        return jsonify({'message': 'Witness added successfully', 'witness_id': new_witness.witnessid}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
@app.route('/api/cases/<int:case_id>/witnesses', methods=['GET'])
@login_required
def get_witnesses_for_case(case_id):
    db = SessionLocal()
    try:
        witness_links = db.query(Witnesscase).filter_by(caseid=case_id).all()
        result = []
        for link in witness_links:
            witness = db.query(Witnesses).filter_by(witnessid=link.witnessid).first()
            if witness:
                result.append({
                    'witness_id': witness.witnessid,
                    'firstname': witness.firstname,
                    'lastname': witness.lastname,
                    'cnic': witness.cnic,
                    'phone': witness.phone,
                    'email': witness.email,
                    'address': witness.address,
                    'pasthistory': witness.pasthistory,
                    'statement': link.statement,
                    'statementdate': link.statementdate.isoformat() if link.statementdate else None
                })
        return jsonify({'witnesses': result}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
        
@app.route('/api/witnesses', methods=['GET'])
@login_required
def get_all_witnesses():
    db = SessionLocal()
    try:
        witnesses = db.query(Witnesses).all()
        if not witnesses:
            return jsonify({'message': 'No witnesses found'}), 404

        result = []
        for witness in witnesses:
            # Get all witness-case relationships
            witness_cases = db.query(Witnesscase).filter_by(witnessid=witness.witnessid).all()

            # Return one or many case records per witness
            if not witness_cases:
                result.append({
                    'witness': {
                        'id': witness.witnessid,
                        'firstname': witness.firstname,
                        'lastname': witness.lastname,
                        'cnic': witness.cnic,
                        'phone': witness.phone,
                        'email': witness.email,
                        'address': witness.address,
                        'pasthistory': witness.pasthistory,
                    },
                    'cases': []
                })
            else:
                for wc in witness_cases:
                    result.append({
                        'witness': {
                            'id': witness.witnessid,
                            'firstname': witness.firstname,
                            'lastname': witness.lastname,
                            'cnic': witness.cnic,
                            'phone': witness.phone,
                            'email': witness.email,
                            'address': witness.address,
                            'pasthistory': witness.pasthistory,
                        },
                        'case_id': wc.caseid,
                        'statement': wc.statement,
                        'statementdate': wc.statementdate
                    })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
@app.route('/api/witnesses/court', methods=['GET'])
@login_required
def get_court_specific_witnesses():
    db = SessionLocal()
    try:
        # Step 1: Get the current user's courtregistrar_id (assuming you have current user id in session)
        userid = current_user.userid  # Implement this method to get the logged-in user's ID

        # Step 2: Get the court_id from the courtregistrar (assuming there's a `CourtRegistrar` model)
        court_registrar = db.query(Courtregistrar).filter_by(userid=userid).first()

        if not court_registrar:
            return jsonify({'message': 'CourtRegistrar not found'}), 404

        # Step 3: Get the courtId associated with the CourtRegistrar
        court_id = court_registrar.courtid

        # Step 4: Fetch court access cases related to the courtId using the manually defined table (t_courtaccess)
        court_access_cases = db.query(t_courtaccess.c.caseid).filter_by(courtid=court_id).all()

        if not court_access_cases:
            return jsonify({"error": "No cases found for this court"}), 404

        # Extract case IDs from court access cases
        case_ids = [case.caseid for case in court_access_cases]  # Accessing attribute of the result object

        # Step 5: Fetch all witnesses associated with these case IDs
        witness_cases = db.query(Witnesscase).filter(Witnesscase.caseid.in_(case_ids)).all()

        # If no witness cases found
        if not witness_cases:
            return jsonify({"message": "No witnesses found for these cases"}), 404

        # Fetching the unique witnesses from witness_cases
        witness_ids = {wc.witnessid for wc in witness_cases}
        witnesses = db.query(Witnesses).filter(Witnesses.witnessid.in_(witness_ids)).all()

        # Prepare the response
        result = []
        for witness in witnesses:
            # Get all witness-case relationships for this witness
            related_cases = [wc for wc in witness_cases if wc.witnessid == witness.witnessid]

            # Return the cases for this witness
            case_data = []
            for wc in related_cases:
                case_data.append({
                    'case_id': wc.caseid,
                    'statement': wc.statement,
                    'statementdate': wc.statementdate
                })

            result.append({
                'witness': {
                    'id': witness.witnessid,
                    'firstname': witness.firstname,
                    'lastname': witness.lastname,
                    'cnic': witness.cnic,
                    'phone': witness.phone,
                    'email': witness.email,
                    'address': witness.address,
                    'pasthistory': witness.pasthistory,
                },
                'cases': case_data
            })

        return jsonify(result), 200

    except Exception as e:
        # Log the error and return a message
        print(f"Error: {e}")
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()




@app.route('/api/witnesses/<int:witness_id>', methods=['DELETE'])
@login_required
# @log_action(action_type = "DELETE", entity_type = "Witnesses")
def delete_witness(witness_id):
    db = SessionLocal()
    try:
        witness = db.query(Witnesses).get(witness_id)
        if not witness:
            return jsonify({'message': 'Witness not found'}), 404

        db.delete(witness)
        db.commit()
        return jsonify({'message': 'Witness deleted successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
# CaseDocument API
@app.route('/api/cases/<int:case_id>/documents', methods=['POST'])
@login_required
# @log_action(action_type = "CREATE (upload a doc)", entity_type = "Documents")
def upload_case_document(case_id):
    db = SessionLocal()
    try:
        file = request.files['file']
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)

        document = Documentcase(
            caseid=case_id,
            documenttitle=filename,
            filepath=filepath,
            submissiondate=datetime.date.today()
        )
        db.add(document)
        db.commit()
        return jsonify({'message': 'Document uploaded successfully', 'document_id': document.documentid}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
@app.route('/api/cases/<int:case_id>/documents', methods=['GET'])
@login_required
def get_case_documents(case_id):
    db = SessionLocal()
    try:
        document_links = db.query(Documentcase).filter_by(caseid=case_id).all()
        result = []
        for link in document_links:
            doc = db.query(Documents).filter_by(documentid=link.documentid).first()
            if doc:
                result.append({
                    'id': doc.documentid,
                    'title': doc.documenttitle,
                    'path': doc.filepath,
                    'uploadDate': doc.uploaddate.isoformat() if doc.uploaddate else '',
                    'type': doc.documenttype or (doc.documenttitle.split('.')[-1] if doc.documenttitle and '.' in doc.documenttitle else 'Document'),
                    'submissiondate': link.submissiondate.isoformat() if link.submissiondate else ''
                })
        return jsonify({'documents': result}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
@app.route('/api/documents', methods=['POST'])
def upload_document():
    data = request.get_json()

    required_fields = ['documenttitle', 'documenttype', 'uploaddate']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        insert_query = """
            INSERT INTO documents (documenttitle, documenttype, uploaddate)
            VALUES (%s, %s, %s)
            RETURNING documentid;
        """
        cur.execute(insert_query, (
            data['documenttitle'],
            data['documenttype'],
            datetime.datetime.strptime(data['uploaddate'], '%Y-%m-%dT%H:%M:%S.%fZ'),
            # data['lawyerid']
        ))

        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'message': 'Document uploaded successfully', 'document_id': new_id}), 201

    except Exception as e:
        logging.error("Error in uploading documents:", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents', methods=['GET'])
@login_required
def get_documents():
    user_id = current_user.userid
    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401

    conn = get_pg_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        query = """
            SELECT d.documenttitle, d.documenttype, d.uploaddate
            FROM documents d
            JOIN documentcase cd ON d.documentid = cd.documentid
            JOIN caselawyeraccess la ON cd.caseid = la.caseid
            JOIN lawyer l ON la.lawyerid = l.lawyerid
            WHERE l.userid = %s
            ORDER BY d.uploaddate DESC
        """
        cur.execute(query, (user_id,))
        documents = cur.fetchall()

        # Convert datetime to ISO format string
        for doc in documents:
            if isinstance(doc['uploaddate'], datetime.datetime):
                doc['uploaddate'] = doc['uploaddate'].isoformat()

        return jsonify({"documents": documents})
    except Exception as e:
        print("Error fetching documents:", e)
        return jsonify({"error": "Failed to fetch documents"}), 500
    finally:
        cur.close()
        conn.close()
        
@app.route('/api/clientdocuments', methods=['GET'])
@login_required
def get_client_documents():
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        query = """
        SELECT DISTINCT
            d.documentid AS id,
            d.documenttitle AS title,
            to_char(d.uploaddate, 'YYYY-MM-DD') AS uploadDate,
            d.documenttype,
            d.documenttype AS fileType,
            d.filepath AS path
        FROM caseparticipant cp
        JOIN caseparticipantaccess cpa ON cp.participantid = cpa.participantid
        JOIN documentcase dc ON dc.caseid = cpa.caseid
        JOIN documents d ON d.documentid = dc.documentid
        WHERE cp.userid = %s
        ORDER BY uploadDate DESC;
        """

        cur.execute(query, (current_user.userid,))
        rows = cur.fetchall()

        documents = []
        for row in rows:
            documents.append({
                "id": row[0],
                "title": row[1],
                "uploadDate": row[2],
                "documenttype": row[3],
                "fileType": row[4],
                "path": row[5],
            })

        cur.close()
        conn.close()

        return jsonify(success=True, documents=documents), 200

    except Exception as e:
        print("Error fetching client documents:", e)
        return jsonify(success=False, message=str(e)), 500

@app.route('/api/documents/<int:document_id>', methods=['DELETE'])
@login_required
# @log_action(action_type = "DELETE", entity_type = "Documents")
def delete_case_document(document_id):
    db = SessionLocal()
    try:
        document = db.query(Documentcase).get(document_id)
        if not document:
            return jsonify({'message': 'Document not found'}), 404

        db.delete(document)
        db.commit()
        return jsonify({'message': 'Document deleted successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@app.route('/api/cases/<int:case_id>/final-decision', methods=['POST'])
@login_required
def add_final_decision(case_id):
    conn = None
    cur = None
    try:
        data = request.get_json()
        decision_summary = data.get('decisionsummary')
        verdict = data.get('verdict')
        decision_date = data.get('decisiondate') or datetime.date.today().isoformat()

        if not decision_summary or not verdict:
            return jsonify({'message': 'Decision summary and verdict are required'}), 400

        # Establish raw connection
        conn = get_pg_connection()
        cur = conn.cursor()

        # Check if case exists
        cur.execute("SELECT 1 FROM cases WHERE caseid = %s", (case_id,))
        if not cur.fetchone():
            return jsonify({'message': 'Case not found'}), 404

        # Insert final decision
        cur.execute("""
            INSERT INTO finaldecision (caseid, decisionsummary, verdict, decisiondate)
            VALUES (%s, %s, %s, %s)
            RETURNING decisionid
        """, (case_id, decision_summary, verdict, decision_date))

        decision_id = cur.fetchone()[0]
        conn.commit()
        
        update_query = """
    UPDATE cases SET status = 'Closed' WHERE caseid = %s
"""
        cur.execute(update_query, (case_id,))
        
        # After inserting finaldecision and updating case status
        cur.execute("""
        INSERT INTO casehistory (caseid, actiondate, actiontaken, remarks)
        VALUES (%s, %s, %s, %s)
        """, (case_id, decision_date, f"Case closed with verdict: {verdict}", decision_summary))

        conn.commit()

        return jsonify({
            'message': 'Final decision added successfully',
            'decision_id': decision_id
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'message': str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/cases/<int:case_id>/final-decision', methods=['GET'])
@login_required
def get_final_decision(case_id):
    db = SessionLocal()
    try:
        final_decision = db.query(Finaldecision).filter_by(caseid=case_id).first()
        if not final_decision:
            return jsonify({'message': 'Final decision not found'}), 404

        return jsonify({
            'decision_id': final_decision.decisionid,
            'case_id': final_decision.caseid,
            'decision_summary': final_decision.decisionsummary,
            'verdict': final_decision.verdict,
            'decision_date': final_decision.decisiondate.isoformat()
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
        
@app.route('/api/finaldecision', methods=['POST'])
def insert_final_decision():
    data = request.get_json()

    required_fields = ['casename', 'verdict', 'decisiondate', 'decisionsummary']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    casename = data['casename']
    verdict = data['verdict']
    decisiondate = data['decisiondate']
    decisionsummary = data['decisionsummary']

    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        # Step 1: Get case ID from casename
        cur.execute("SELECT caseid FROM cases WHERE title = %s", (casename,))
        case = cur.fetchone()

        if not case:
            return jsonify({"error": "Case not found"}), 404

        caseid = case[0]

        # Step 2: Insert into finaldecision
        insert_query = """
            INSERT INTO finaldecision (caseid, verdict, decisiondate, decisionsummary)
            VALUES (%s, %s, %s, %s)
            RETURNING finaldecisionid
        """
        cur.execute(insert_query, (caseid, verdict, decisiondate, decisionsummary))
        finaldecision_id = cur.fetchone()[0]

        conn.commit()
        cur.close()
        return jsonify({"message": "Final decision submitted", "id": finaldecision_id}), 201

    except Exception as e:
        print("Error:", e)
        print(traceback.format_exc())
        if conn:
            conn.rollback()
        return jsonify({"error": "Failed to insert final decision"}), 500
    finally:
        if conn:
            conn.close()        
        
@app.route('/api/final-decision/<int:decision_id>', methods=['PUT'])
@login_required
# @log_action(action_type = "UPDATE", entity_type = "FinalDecision")
def update_final_decision(decision_id):
    db = SessionLocal()
    try:
        data = request.get_json()
        final_decision = db.query(Finaldecision).get(decision_id)

        if not final_decision:
            return jsonify({'message': 'Final decision not found'}), 404

        final_decision.decisionsummary = data.get('decisionsummary', final_decision.decisionsummary)
        final_decision.verdict = data.get('verdict', final_decision.verdict)
        final_decision.decisiondate = data.get('decisiondate', final_decision.decisiondate)

        db.commit()
        return jsonify({'message': 'Final decision updated successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

#Remand API
@app.route('/api/cases/<int:case_id>/remands', methods=['POST'])
@login_required
# @log_action(action_type = "CREATE", entity_type = "Remands")
def add_remand(case_id):
    db = SessionLocal()
    try:
        data = request.get_json()
        start_date = data.get('startdate')
        end_date = data.get('enddate')
        remand_type = data.get('remandtype')
        remand_reason = data.get('remandreason')

        if not start_date or not end_date or not remand_type:
            return jsonify({'message': 'Start date, end date, and remand type are required'}), 400

        # Check if the case exists
        case = db.query(Cases).get(case_id)
        if not case:
            return jsonify({'message': 'Case not found'}), 404

        # Add remand
        new_remand = Remands(
            caseid=case_id,
            startdate=start_date,
            enddate=end_date,
            remandtype=remand_type,
            remandreason=remand_reason
        )
        db.add(new_remand)
        db.commit()

        return jsonify({'message': 'Remand added successfully', 'remand_id': new_remand.remandid}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@app.route('/api/cases/<int:case_id>/remands', methods=['GET'])
@login_required
def get_remands_for_case(case_id):
    db = SessionLocal()
    try:
        remands = db.query(Remands).filter_by(caseid=case_id).all()
        result = [
            {
                'remand_id': r.remandid,
                'start_date': r.startdate.isoformat(),
                'end_date': r.enddate.isoformat(),
                'remand_type': r.remandtype,
                'remand_reason': r.remandreason
            }
            for r in remands
        ]
        return jsonify({'remands': result}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@app.route('/api/remands/<int:remand_id>', methods=['PUT'])
@login_required

def update_remand(remand_id):
    db = SessionLocal()
    try:
        data = request.get_json()
        remand = db.query(Remands).get(remand_id)

        if not remand:
            return jsonify({'message': 'Remand not found'}), 404

        remand.startdate = data.get('startdate', remand.startdate)
        remand.enddate = data.get('enddate', remand.enddate)
        remand.remandtype = data.get('remandtype', remand.remandtype)
        remand.remandreason = data.get('remandreason', remand.remandreason)

        db.commit()
        return jsonify({'message': 'Remand updated successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
        
@app.route('/api/remands', methods=['GET'])
@login_required
def get_remands():
    user_id = current_user.userid

    query = """
        WITH courtregistrar AS (
            SELECT registrarid AS registrarid, courtid
            FROM courtregistrar
            WHERE userid = %s
        ),
        caseids AS (
            SELECT ca.caseid
            FROM courtaccess ca
            JOIN courtregistrar r ON ca.courtid = r.courtid
        )
        SELECT
            c.title AS casename,
            r.remandtype,
            r.remanddate,
            r.remandreason,
            r.status,
            (r.enddate - r.startdate) || ' days' AS duration
        FROM remands r
        JOIN caseids ci ON r.caseid = ci.caseid
        JOIN cases c ON c.caseid = r.caseid
    """

    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, (user_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # Map rows to match frontend schema
        remands = []
        for idx, row in enumerate(rows, 1):
            remands.append({
                "id": idx,
                "title": row["casename"],
                "lawyername": "-",  # Placeholder or extend with JOIN
                "clientname": "-",  # Placeholder or extend with JOIN
                "remandtype": row["remandtype"],
                "remanddate": row["remanddate"],
                "remandreason": row["remandreason"],
                "status": row["status"],
                "duration": row["duration"]
            })

        return jsonify(remands), 200

    except Exception as e:
        print("Error fetching remands:", e)
        return jsonify({'error': 'Failed to fetch remands'}), 500

@app.route('/api/remands', methods=['POST'])
@login_required
def create_remand():
    data = request.get_json()

    case_title = data.get("caseName")
    remand_type = data.get("remandType")
    remand_date = data.get("remandDate")
    remand_reason = data.get("remandReason")
    status = data.get("status")
    duration_days = int(data.get("duration", 0))

    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Get caseid by case title
        cur.execute("SELECT caseid FROM cases WHERE title = %s", (case_title,))
        case_row = cur.fetchone()
        if not case_row:
            return jsonify({'error': 'Case not found'}), 404
        case_id = case_row['caseid']

        # Calculate dates
        start_date = datetime.datetime.strptime(remand_date, '%Y-%m-%d')
        end_date = start_date + datetime.timedelta(days=duration_days)

        # Insert remand
        cur.execute("""
            INSERT INTO remands (caseid, remandtype, remanddate, remandreason, status, startdate, enddate)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING remandid
        """, (case_id, remand_type, remand_date, remand_reason, status, start_date.date(), end_date.date()))
        remand_id = cur.fetchone()['remandid']

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "id": remand_id,
            "caseName": case_title,
            "lawyerName": "-",  # You can extend with join
            "clientName": "-",
            "remandType": remand_type,
            "remandDate": remand_date,
            "remandReason": remand_reason,
            "status": status,
            "duration": f"{duration_days} days"
        }), 201

    except Exception as e:
        print("Error inserting remand:", e)
        return jsonify({'error': 'Failed to create remand'}), 500
    
    
@app.route('/api/judges', methods=['POST'])
@login_required
def create_judge():
    data = request.get_json()

    full_name = data.get("name", "")
    position = data.get("position")
    expyears = data.get("experience")
    appointment_date = data.get("appointmentDate")
    specialization = data.get("specialization")
    assigned_titles = data.get("assignedCases", [])

    try:
        # Split name
        parts = full_name.strip().split()
        firstname = parts[0]
        lastname = ' '.join(parts[1:]) if len(parts) > 1 else ''

        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Get the courtid via the logged-in registrar
        cur.execute("SELECT courtid FROM courtregistrar WHERE userid = %s", (current_user.userid,))
        reg_row = cur.fetchone()
        if not reg_row:
            return jsonify({"error": "Registrar not assigned to court"}), 403
        courtid = reg_row["courtid"]

        # Insert user
        cur.execute("""
            INSERT INTO users (firstname, lastname, role)
            VALUES (%s, %s, 'Judge')
            RETURNING userid
        """, (firstname, lastname))
        userid = cur.fetchone()['userid']

        # Insert judge
        cur.execute("""
            INSERT INTO judge (userid, position, expyears, appointmentdate, specialization)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING judgeid
        """, (userid, position, expyears, appointment_date, specialization))
        judgeid = cur.fetchone()['judgeid']

        # Assign judge to court
        cur.execute("INSERT INTO judgeworksin (judgeid, courtid) VALUES (%s, %s)", (judgeid, courtid))

        # Assign judge to cases (lookup caseids)
        for title in assigned_titles:
            cur.execute("SELECT caseid FROM cases WHERE title = %s", (title,))
            case_row = cur.fetchone()
            if case_row:
                cur.execute("INSERT INTO judgeaccess (judgeid, caseid) VALUES (%s, %s)", (judgeid, case_row['caseid']))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "judgeid": judgeid,
            "name": full_name,
            "position": position,
            "expyears": expyears,
            "appointmentdate": appointment_date,
            "specialization": specialization,
            "assigned_cases": assigned_titles
        }), 201

    except Exception as e:
        print("Error creating judge:", e)
        return jsonify({'error': 'Failed to create judge'}), 500
    
@app.route('/api/remands/<int:remand_id>', methods=['DELETE'])
@login_required

def delete_remand(remand_id):
    db = SessionLocal()
    try:
        remand = db.query(Remands).get(remand_id)
        if not remand:
            return jsonify({'message': 'Remand not found'}), 404

        db.delete(remand)
        db.commit()
        return jsonify({'message': 'Remand deleted successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()
        
def check_case_access(case_id):
    db = SessionLocal()
    try:
        query = db.query(Cases).filter_by(caseid=case_id)

        if current_user.role == 'Lawyer':
            lawyer = db.query(Lawyer).filter_by(userid=current_user.userid).first()
            if not lawyer:
                return False
            query = query.filter(Cases.lawyerid == lawyer.lawyerid)

        elif current_user.role == 'CaseParticipant':
            participant = db.query(Caseparticipant).filter_by(userid=current_user.userid).first()
            if not participant:
                return False
            query = query.filter(Cases.caseid.in_(
                db.query(Caseparticipant.caseid).filter_by(userid=current_user.userid)
            ))

        elif current_user.role == 'CourtRegistrar':
            registrar = db.query(Courtregistrar).filter_by(userid=current_user.userid).first()
            if not registrar or not registrar.courtid:
                return False
            query = query.filter(Cases.caseid.in_(
                db.query(t_courtaccess.c.caseid).filter_by(courtid=registrar.courtid)
            ))

        return query.first() is not None
    finally:
        db.close()

@app.route('/api/logs', methods=['GET'])
def get_logs():
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

        logs_data = []
        for row in rows:
            logs_data.append({
                'logid': row['logid'],
                'adminid': row['adminid'],
                'actiontype': row['actiontype'],
                'description': row['description'],
                'status': row['status'],
                'actiontimestamp': row['actiontimestamp'],
                'entitytype': row['entitytype'],
                'admin': {
                    'adminid': row['admin_adminid'],
                    
                }
            })

        cur.close()
        conn.close()
        return jsonify(logs_data), 200

    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'error': str(e)}), 500

    
@app.route('/api/logs/activity', methods=['GET'])
@login_required
def get_dashboard_activity_logs():
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("""
            SELECT 
                l.description,
                l.entitytype,
                l.actiontimestamp
            FROM logtable l
            WHERE l.entitytype IN ('case', 'prosecutor', 'casehistory', 'finaldecision', 'lawyer', 'judge')
            ORDER BY l.actiontimestamp DESC
            LIMIT 7
        """)
        rows = cur.fetchall()

        activity_logs = []
        for row in rows:
            activity_logs.append({
                'activity': row['description'],
                'type': row['entitytype'],
                'timestamp': row['actiontimestamp'].strftime("%Y-%m-%d %I:%M %p")
            })

        cur.close()
        conn.close()
        return jsonify(activity_logs), 200

    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/adminprofile', methods=['GET'])
def get_admin_profile():
    db = SessionLocal()
    user_id = current_user.userid  
    
    if not user_id:
        return jsonify(success=False, message="User ID is required."), 400

    return jsonify(success=True, data={
        'firstName': current_user.firstname,
        'lastName': current_user.lastname,
        'email': current_user.email,
        'phone': current_user.phoneno,
        'cnic': current_user.cnic,
        'dob': current_user.dob.isoformat() if current_user.dob else '',
        
    })
    

@app.route('/api/verifycases', methods=['POST'])
def verify_cases():
    data = request.get_json()

    required_fields = ['casename', 'type', 'filingdate', 'clientname', 'lawyername', 'judgename']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    casename = data['casename']
    clientname = data['clientname']
    lawyername = data['lawyername']
    judgename = data['judgename']
    prosecutorname = data.get('prosecutorname')

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        # Get caseid
        cur.execute("SELECT caseid FROM cases WHERE title = %s", (casename,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Case not found"}), 404
        caseid = row[0]

        # Get userids
        def get_userid_by_name(fullname):
            first, last = fullname.split(maxsplit=1)
            cur.execute("SELECT userid FROM users WHERE firstname = %s AND lastname = %s", (first, last))
            result = cur.fetchone()
            return result[0] if result else None

        client_userid = get_userid_by_name(clientname)
        lawyer_userid = get_userid_by_name(lawyername)
        judge_userid = get_userid_by_name(judgename)
        prosecutor_userid = get_userid_by_name(prosecutorname) if prosecutorname else None

        if not all([client_userid, lawyer_userid, judge_userid]):
            return jsonify({"error": "Client, Lawyer, or Judge not found"}), 404

        # Get participantid for client
        cur.execute("SELECT participantid FROM caseparticipant WHERE userid = %s", (client_userid,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Client caseparticipant not found"}), 404
        participantid = row[0]

        # Get lawyerid
        cur.execute("SELECT lawyerid FROM lawyer WHERE userid = %s", (lawyer_userid,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Lawyer not found"}), 404
        lawyerid = row[0]

        # Get judgeid
        cur.execute("SELECT judgeid FROM judge WHERE userid = %s", (judge_userid,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Judge not found"}), 404
        judgeid = row[0]

        # Get prosecutorid (optional)
        prosecutorid = None
        if prosecutor_userid:
            cur.execute("SELECT prosecutorid FROM prosecutor WHERE name = %s", (prosecutorname,))
            row = cur.fetchone()
            if row:
                prosecutorid = row[0]

        # Insert caseparticipantaccess
        cur.execute("INSERT INTO caseparticipantaccess (caseid, participantid) VALUES (%s, %s) ON CONFLICT DO NOTHING", (caseid, participantid))

        # Insert caselawyeraccess
        cur.execute("INSERT INTO caselawyeraccess (caseid, lawyerid) VALUES (%s, %s) ON CONFLICT DO NOTHING", (caseid, lawyerid))

        # Insert judgeaccess
        cur.execute("INSERT INTO judgeaccess (caseid, judgeid) VALUES (%s, %s) ON CONFLICT DO NOTHING", (caseid, judgeid))

        # Insert prosecutorassign (optional)
        if prosecutorid:
            cur.execute("INSERT INTO prosecutorassign (caseid, prosecutorid) VALUES (%s, %s) ON CONFLICT DO NOTHING", (caseid, prosecutorid))

        conn.commit()
        return jsonify({"message": "Case verified and relationships created."}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    app.run(debug=True)
