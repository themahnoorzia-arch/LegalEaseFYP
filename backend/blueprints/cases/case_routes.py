import datetime
import logging

from flask import jsonify, request
from flask_login import login_required, current_user

import psycopg2.extras
from sqlalchemy.orm import aliased

from blueprints.cases import cases_bp
from db.db import SessionLocal, get_pg_connection

from models import (
    Cases,
    Lawyer,
    Judge,
    Court,
    Courtregistrar,
    Caseparticipant,
    Prosecutor,
    Payments,
    Remands,
    Evidence,
    Witnesses,
    Witnesscase,
    Casehistory,
    Finaldecision,
    Users,
    t_courtaccess,
    t_caseparticipantaccess,
    t_caselawyeraccess,
    t_judgeaccess,
    t_prosecutorassign,
)


def _serialize_lawyer_case(db, case):
    court_names = [
        court.courtname for court in case.court if court.courtname
    ]
    court_name_str = ", ".join(court_names) if court_names else "N/A"

    prosecutor_name = "N/A"
    prosecutor_rows = db.execute(
        t_prosecutorassign.select().where(
            t_prosecutorassign.c.caseid == case.caseid
        )
    ).fetchall()
    if prosecutor_rows:
        prosecutor = db.query(Prosecutor).filter_by(
            prosecutorid=prosecutor_rows[0].prosecutorid
        ).first()
        if prosecutor:
            prosecutor_name = prosecutor.name

    judge_name = "N/A"
    if case.judge:
        judge = case.judge[0]
        if judge.users:
            judge_name = (
                f"{judge.users.firstname or ''} "
                f"{judge.users.lastname or ''}"
            ).strip()

    history = [
        {
            "date": h.actiondate.isoformat() if h.actiondate else None,
            "event": h.actiontaken,
        }
        for h in case.casehistory
    ]

    decision_data = {}
    if case.finaldecision:
        fd = case.finaldecision[0]
        decision_data = {
            "decisionId": fd.decisionid,
            "verdict": fd.verdict or "",
            "decisionSummary": fd.decisionsummary or "",
            "decisionDate": (
                fd.decisiondate.isoformat() if fd.decisiondate else ""
            ),
        }

    remand = db.query(Remands).filter_by(caseid=case.caseid).first()
    remand_status = remand.status if remand else "N/A"

    client_name = "N/A"
    access_row = db.execute(
        t_caseparticipantaccess.select().where(
            t_caseparticipantaccess.c.caseid == case.caseid
        )
    ).first()
    if access_row:
        participant = db.query(Caseparticipant).filter_by(
            participantid=access_row.participantid
        ).first()
        if participant:
            client_user = db.query(Users).filter_by(
                userid=participant.userid
            ).first()
            if client_user:
                client_name = (
                    f"{client_user.firstname or ''} "
                    f"{client_user.lastname or ''}"
                ).strip()

    return {
        "caseid": case.caseid,
        "title": case.title,
        "description": case.description,
        "casetype": case.casetype,
        "filingdate": (
            case.filingdate.isoformat() if case.filingdate else None
        ),
        "status": case.status,
        "clientname": client_name,
        "courtname": court_name_str,
        "judgeName": judge_name,
        "prosecutorName": prosecutor_name,
        "remandstatus": remand_status,
        "decisionId": decision_data.get("decisionId", ""),
        "decisiondate": decision_data.get("decisionDate", ""),
        "decisionsummary": decision_data.get("decisionSummary", ""),
        "verdict": decision_data.get("verdict", ""),
        "history": history,
    }


def _serialize_registrar_case(db, case):
    """Return case data enriched with client, lawyer, judge, prosecutor names
    for the CourtRegistrar dashboard view."""

    # Client name from caseparticipantaccess → caseparticipant → users
    client_name = "N/A"
    access_row = db.execute(
        t_caseparticipantaccess.select().where(
            t_caseparticipantaccess.c.caseid == case.caseid
        )
    ).first()
    if access_row:
        participant = db.query(Caseparticipant).filter_by(
            participantid=access_row.participantid
        ).first()
        if participant and participant.userid:
            client_user = db.query(Users).filter_by(
                userid=participant.userid
            ).first()
            if client_user:
                client_name = (
                    f"{client_user.firstname or ''} "
                    f"{client_user.lastname or ''}"
                ).strip() or "N/A"

    # Lead / first lawyer linked to the case
    lawyer_name = "N/A"
    if case.lawyer:
        lw = case.lawyer[0]
        if lw.users:
            lawyer_name = (
                f"{lw.users.firstname or ''} "
                f"{lw.users.lastname or ''}"
            ).strip() or "N/A"

    # Assigned judge
    judge_name = "N/A"
    if case.judge:
        jg = case.judge[0]
        if jg.users:
            judge_name = (
                f"{jg.users.firstname or ''} "
                f"{jg.users.lastname or ''}"
            ).strip() or "N/A"

    # Assigned prosecutor
    prosecutor_name = "N/A"
    if case.prosecutor:
        prosecutor_name = case.prosecutor[0].name or "N/A"

    return {
        "caseid": case.caseid,
        "title": case.title,
        "description": case.description,
        "casetype": case.casetype,
        "filingdate": case.filingdate.isoformat() if case.filingdate else None,
        "status": case.status,
        "casenumber": case.casenumber,
        "clientname": client_name,
        "lawyername": lawyer_name,
        "judgeName": judge_name,
        "prosecutor": prosecutor_name,
    }


@cases_bp.route('/cases', methods=['POST'])
@login_required
def create_case():

    conn = None

    try:

        data = request.get_json()

        title = data.get('title')
        description = data.get('description')
        casetype = data.get('casetype')
        casenumber = data.get('casenumber')
        side = data.get('side', '').strip().lower()
        filingdate = (
            data.get('filingdate')
            or datetime.date.today()
        )

        courtname = data.get('courtname')
        fullname = data.get(
            'clientName',
            ''
        ).strip()

        required_fields = {
            'title': title,
            'casetype': casetype,
            'side': side,
            'courtname': courtname,
            'clientName': fullname,
        }

        missing_fields = [
            key for key, value in required_fields.items() if not value
        ]

        if missing_fields:
            return jsonify({
                'message': 'Missing required fields',
                'missing': missing_fields
            }), 400

        parts = fullname.split()

        if len(parts) < 2:
            return jsonify({
                'message':
                'Please provide full name'
            }), 400

        firstname = parts[0]
        lastname = " ".join(parts[1:])

        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Get lawyer profile early
        cur.execute(
            "SELECT lawyerid FROM lawyer WHERE userid = %s",
            (current_user.userid,)
        )
        lawyer_row = cur.fetchone()
        if not lawyer_row:
            return jsonify({'message': 'Lawyer profile not found'}), 404

        lawyerid = lawyer_row.get('lawyerid') if isinstance(lawyer_row, dict) else lawyer_row[0]

        cur.execute(
            """
            SELECT courtid
            FROM court
            WHERE courtname=%s
            """,
            (courtname,)
        )

        court_row = cur.fetchone()
        if not court_row:
            return jsonify({
                'message':
                'Court not found'
            }), 404

        courtid = court_row['courtid']

        # Duplicate check — only by case number (if provided)
        # The similarity()-based check was removed because it requires pg_trgm
        # and was incorrectly matching unrelated cases.
        duplicate_case = None
        if casenumber:
            cur.execute(
                "SELECT caseid FROM cases WHERE casenumber = %s LIMIT 1",
                (casenumber,)
            )
            duplicate_case = cur.fetchone()

        # Check if caselawyeraccess has a status column
        cur.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='caselawyeraccess' AND column_name='status'"
        )
        has_status = cur.fetchone() is not None

        if duplicate_case:
            existing_caseid = duplicate_case['caseid'] if isinstance(duplicate_case, dict) else duplicate_case[0]
            if has_status:
                cur.execute(
                    """
                    INSERT INTO caselawyeraccess (caseid, lawyerid, side, is_lead, status)
                    VALUES (%s, %s, %s, TRUE, 'approved')
                    ON CONFLICT (caseid, lawyerid) DO UPDATE
                    SET side = EXCLUDED.side, status = EXCLUDED.status
                    """,
                    (existing_caseid, lawyerid, side),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO caselawyeraccess (caseid, lawyerid, side, is_lead)
                    VALUES (%s, %s, %s, TRUE)
                    ON CONFLICT (caseid, lawyerid) DO UPDATE
                    SET side = EXCLUDED.side
                    """,
                    (existing_caseid, lawyerid, side),
                )
            conn.commit()
            return jsonify({
                'message': 'Joined existing case',
                'case_id': existing_caseid
            }), 200

        cur.execute(
            """
            INSERT INTO cases
            (
                title,
                description,
                casetype,
                casenumber,
                filingdate,
                status
            )
            VALUES
            (
                %s,%s,%s,%s,%s,'Pending'
            )
            RETURNING caseid
            """,
            (
                title,
                description,
                casetype,
                casenumber,
                filingdate
            )
        )

        row = cur.fetchone()
        if isinstance(row, dict):
            caseid = row.get('caseid')
        else:
            caseid = row[0] if row is not None else None

        cur.execute(
            """
            INSERT INTO courtaccess
            (
                courtid,
                caseid
            )
            VALUES (%s,%s)
            """,
            (
                courtid,
                caseid
            )
        )

        cur.execute(
            """
            SELECT userid
            FROM users
            WHERE LOWER(firstname)=LOWER(%s)
            AND LOWER(lastname)=LOWER(%s)
            """,
            (
                firstname,
                lastname
            )
        )

        user_row = cur.fetchone()

        if not user_row:
            # Auto-create user as CaseParticipant
            email = f"{firstname.lower()}.{lastname.lower()}@legalease-temp.com"
            cur.execute(
                """
                INSERT INTO users (role, firstname, lastname, email)
                VALUES ('CaseParticipant', %s, %s, %s)
                RETURNING userid
                """,
                (firstname, lastname, email)
            )
            user_row = cur.fetchone()
            userid = user_row.get('userid') if isinstance(user_row, dict) else user_row[0]
            
            cur.execute(
                """
                INSERT INTO caseparticipant (userid, address)
                VALUES (%s, 'Address not specified')
                RETURNING participantid
                """,
                (userid,)
            )
            part_row = cur.fetchone()
            participantid = part_row.get('participantid') if isinstance(part_row, dict) else part_row[0]
        else:
            userid = user_row.get('userid') if isinstance(user_row, dict) else user_row[0]
            cur.execute(
                """
                SELECT participantid
                FROM caseparticipant
                WHERE userid=%s
                """,
                (userid,)
            )
            participant_row = cur.fetchone()
            if not participant_row:
                cur.execute(
                    """
                    INSERT INTO caseparticipant (userid, address)
                    VALUES (%s, 'Address not specified')
                    RETURNING participantid
                    """,
                    (userid,)
                )
                part_row = cur.fetchone()
                participantid = part_row.get('participantid') if isinstance(part_row, dict) else part_row[0]
            else:
                participantid = participant_row.get('participantid') if isinstance(participant_row, dict) else participant_row[0]

        cur.execute(
            """
            INSERT INTO caseparticipantaccess
            (
                participantid,
                caseid
            )
            VALUES (%s,%s)
            """,
            (
                participantid,
                caseid
            )
        )

        # Link lawyer who requested/created the case
        if has_status:
            cur.execute(
                """
                INSERT INTO caselawyeraccess (caseid, lawyerid, side, is_lead, status)
                VALUES (%s, %s, %s, TRUE, 'approved')
                ON CONFLICT (caseid, lawyerid) DO UPDATE
                SET side = EXCLUDED.side, status = EXCLUDED.status
                """,
                (caseid, lawyerid, side),
            )
        else:
            cur.execute(
                """
                INSERT INTO caselawyeraccess (caseid, lawyerid, side, is_lead)
                VALUES (%s, %s, %s, TRUE)
                ON CONFLICT (caseid, lawyerid) DO UPDATE
                SET side = EXCLUDED.side
                """,
                (caseid, lawyerid, side),
            )

        conn.commit()

        from utils.logging import write_log
        write_log("CREATE", f"New case registered: {title}", "case")

        return jsonify({
            'message': 'Case created successfully',
            'case_id': caseid
        }), 201

    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify({
            'message': str(e)
        }), 500

    finally:

        if conn:
            conn.close()


@cases_bp.route('/cases/join-request', methods=['POST'])
@login_required
def join_case_request():
    """Join an existing case as a lawyer. Expects JSON: { caseid, side }"""
    data = request.get_json() or {}
    caseid = data.get('caseid')
    side = (data.get('side') or '').strip().lower()

    if not caseid or not side:
        return jsonify({'message': 'Missing caseid or side'}), 400

    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # verify case exists
        cur.execute("SELECT caseid FROM cases WHERE caseid = %s", (caseid,))
        c = cur.fetchone()
        if not c:
            return jsonify({'message': 'Case not found'}), 404

        # find lawyer profile for current user
        cur.execute("SELECT lawyerid FROM lawyer WHERE userid = %s", (current_user.userid,))
        lawyer_row = cur.fetchone()
        if not lawyer_row:
            return jsonify({'message': 'Lawyer profile not found'}), 404

        lawyerid = lawyer_row['lawyerid']

        cur.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='caselawyeraccess' AND column_name='status'"
        )
        has_status = cur.fetchone() is not None

        if has_status:
            cur.execute(
                """
                INSERT INTO caselawyeraccess (caseid, lawyerid, side, is_lead, status)
                VALUES (%s, %s, %s, TRUE, 'pending')
                ON CONFLICT (caseid, lawyerid) DO UPDATE
                SET side = EXCLUDED.side, status = EXCLUDED.status
                """,
                (caseid, lawyerid, side),
            )
        else:
            cur.execute(
                """
                INSERT INTO caselawyeraccess (caseid, lawyerid, side, is_lead)
                VALUES (%s, %s, %s, TRUE)
                ON CONFLICT (caseid, lawyerid) DO UPDATE
                SET side = EXCLUDED.side
                """,
                (caseid, lawyerid, side),
            )
        conn.commit()

        return jsonify({'message': 'Joined case successfully', 'case_id': caseid}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'message': str(e)}), 500

    finally:
        if conn:
            conn.close()


@cases_bp.route('/cases/check-duplicate', methods=['GET'])
@login_required
def check_duplicate_case():
    query = request.args.get('query', '').strip()

    if not query:
        return jsonify({'matches': []}), 200

    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        like_q = f"%{query}%"
        cur.execute(
            """
            SELECT c.caseid, c.title, c.casenumber, c.status
            FROM cases c
            WHERE c.title ILIKE %s OR c.casenumber ILIKE %s
            ORDER BY c.caseid
            """,
            (like_q, like_q),
        )

        rows = cur.fetchall()
        matches = []
        for row in rows:
            matches.append({
                'caseid': row['caseid'],
                'title': row['title'],
                'casenumber': row.get('casenumber'),
                'status': row.get('status'),
            })

        return jsonify({'matches': matches}), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 500

    finally:
        if conn:
            conn.close()


@cases_bp.route('/casebyid', methods=['GET'])
@login_required
def get_cases_by_id():

    db = SessionLocal()

    try:

        role = current_user.role.lower()
        user_id = current_user.userid

        query = db.query(Cases)

        if role == "lawyer":
            query = query.filter(
                Cases.lawyerid == user_id
            )

        elif role == "judge":
            query = query.filter(
                Cases.judgeid == user_id
            )

        elif role == "client":
            query = query.filter(
                Cases.clientid == user_id
            )

        else:
            return jsonify({
                "message":
                "Invalid role"
            }), 400

        cases = query.all()

        result = []

        for c in cases:

            result.append({
                'caseid': c.caseid,
                'title': c.title,
                'description': c.description,
                'casetype': c.casetype,
                'filingdate':
                    c.filingdate.isoformat()
                    if c.filingdate
                    else None,
                'status': c.status,
            })

        return jsonify({
            'cases': result
        })

    finally:
        db.close()


@cases_bp.route('/cases/<int:case_id>', methods=['PUT'])
@login_required
def update_case(case_id):

    db = SessionLocal()

    try:

        data = request.get_json()

        case = db.query(Cases).get(case_id)

        if not case:
            return jsonify({
                'message':
                'Case not found'
            }), 404

        case.title = data.get(
            'title',
            case.title
        )

        case.description = data.get(
            'description',
            case.description
        )

        case.casetype = data.get(
            'casetype',
            case.casetype
        )

        case.status = data.get(
            'status',
            case.status
        )

        db.commit()

        return jsonify({
            'message':
            'Case updated successfully'
        })

    except Exception as e:

        db.rollback()

        return jsonify({
            'message': str(e)
        }), 500

    finally:

        db.close()


@cases_bp.route('/cases/<int:case_id>', methods=['DELETE'])
@login_required
def delete_case(case_id):

    db = SessionLocal()

    try:

        case = db.query(Cases).get(case_id)

        if not case:
            return jsonify({
                'message':
                'Case not found'
            }), 404

        db.delete(case)

        db.commit()

        return jsonify({
            'message':
            'Case deleted successfully'
        })

    except Exception as e:

        db.rollback()

        return jsonify({
            'message': str(e)
        }), 500

    finally:

        db.close()

@cases_bp.route('/cases', methods=['GET'])
@login_required
def get_cases():

    db = SessionLocal()

    try:

        role = current_user.role

        if role == "Lawyer":

            lawyer = (
                db.query(Lawyer)
                .filter_by(userid=current_user.userid)
                .first()
            )

            if not lawyer:
                return jsonify({"cases": []}), 200

            cases = (
                db.query(Cases)
                .join(
                    t_caselawyeraccess,
                    Cases.caseid == t_caselawyeraccess.c.caseid,
                )
                .filter(
                    t_caselawyeraccess.c.lawyerid == lawyer.lawyerid
                )
                .all()
            )

            result = [
                _serialize_lawyer_case(db, case) for case in cases
            ]
            return jsonify({"cases": result}), 200

        elif role == "CaseParticipant":

            participant = (
                db.query(Caseparticipant)
                .filter_by(userid=current_user.userid)
                .first()
            )

            if not participant:
                return jsonify({"cases": []}), 200

            cases = (
                db.query(Cases)
                .join(
                    t_caseparticipantaccess,
                    Cases.caseid == t_caseparticipantaccess.c.caseid,
                )
                .filter(
                    t_caseparticipantaccess.c.participantid
                    == participant.participantid
                )
                .all()
            )

            client_result = []
            for c in cases:
                court_names = [
                    court.courtname for court in c.court if court.courtname
                ]
                lawyer_names = []
                for lawyer in c.lawyer:
                    if lawyer.users:
                        lawyer_names.append(
                            f"{lawyer.users.firstname or ''} "
                            f"{lawyer.users.lastname or ''}".strip()
                        )
                history = [
                    {
                        "date": h.actiondate.isoformat() if h.actiondate else None,
                        "event": h.actiontaken,
                    }
                    for h in c.casehistory
                ]
                final_decision = None
                if c.finaldecision:
                    fd = c.finaldecision[0]
                    final_decision = {
                        "verdict": fd.verdict,
                        "summary": fd.decisionsummary,
                        "date": (
                            fd.decisiondate.isoformat()
                            if fd.decisiondate
                            else None
                        ),
                    }
                evidence = [
                    {
                        "id": e.evidenceid,
                        "type": e.evidencetype,
                        "description": e.description,
                        "submittedDate": (
                            e.submitteddate.isoformat()
                            if e.submitteddate
                            else None
                        ),
                        "evidencePath": e.filepath,
                    }
                    for e in c.evidence
                ]
                witness_links = (
                    db.query(Witnesscase).filter_by(caseid=c.caseid).all()
                )
                witnesses = []
                for link in witness_links:
                    witness = (
                        db.query(Witnesses)
                        .filter_by(witnessid=link.witnessid)
                        .first()
                    )
                    if witness:
                        witnesses.append({
                            "id": witness.witnessid,
                            "firstName": witness.firstname,
                            "lastName": witness.lastname,
                            "cnic": witness.cnic,
                            "phone": witness.phone,
                            "email": witness.email,
                            "address": witness.address,
                            "pastHistory": witness.pasthistory,
                        })
                client_result.append({
                    "id": c.caseid,
                    "caseid": c.caseid,
                    "title": c.title,
                    "description": c.description,
                    "caseType": c.casetype,
                    "casetype": c.casetype,
                    "filingDate": (
                        c.filingdate.isoformat() if c.filingdate else None
                    ),
                    "filingdate": (
                        c.filingdate.isoformat() if c.filingdate else None
                    ),
                    "status": c.status,
                    "lawyers": " & ".join(lawyer_names) or "N/A",
                    "courtName": ", ".join(court_names) if court_names else "N/A",
                    "nextHearing": "N/A",
                    "finalDecision": final_decision,
                    "history": history,
                    "evidence": evidence,
                    "witnesses": witnesses,
                })
            return jsonify({"cases": client_result}), 200

        elif role == "Judge":

            judge = (
                db.query(Judge)
                .filter_by(userid=current_user.userid)
                .first()
            )

            if not judge:
                return jsonify({"cases": []}), 200

            cases = (
                db.query(Cases)
                .join(
                    t_judgeaccess,
                    Cases.caseid == t_judgeaccess.c.caseid,
                )
                .filter(t_judgeaccess.c.judgeid == judge.judgeid)
                .all()
            )

            judge_result = []
            for c in cases:
                court_names = [
                    court.courtname for court in c.court if court.courtname
                ]
                lawyer_names = []
                for lawyer in c.lawyer:
                    if lawyer.users:
                        lawyer_names.append(
                            f"{lawyer.users.firstname or ''} "
                            f"{lawyer.users.lastname or ''}".strip()
                        )
                history = [
                    {
                        "date": h.actiondate.isoformat() if h.actiondate else None,
                        "event": h.actiontaken,
                    }
                    for h in c.casehistory
                ]
                final_decision = None
                if c.finaldecision:
                    fd = c.finaldecision[0]
                    final_decision = {
                        "verdict": fd.verdict,
                        "summary": fd.decisionsummary,
                        "date": (
                            fd.decisiondate.isoformat()
                            if fd.decisiondate
                            else None
                        ),
                    }
                judge_result.append({
                    "id": c.caseid,
                    "caseid": c.caseid,
                    "title": c.title,
                    "description": c.description,
                    "caseType": c.casetype,
                    "casetype": c.casetype,
                    "filingDate": (
                        c.filingdate.isoformat() if c.filingdate else None
                    ),
                    "status": c.status,
                    "lawyers": " & ".join(lawyer_names) or "N/A",
                    "courtName": ", ".join(court_names) if court_names else "N/A",
                    "history": history,
                    "evidence": [
                        {
                            "id": e.evidenceid,
                            "type": e.evidencetype,
                            "description": e.description,
                            "submittedDate": (
                                e.submitteddate.isoformat()
                                if e.submitteddate
                                else None
                            ),
                            "evidencePath": e.filepath,
                        }
                        for e in c.evidence
                    ],
                    "witnesses": [],
                    "finalDecision": final_decision,
                })
            return jsonify({"cases": judge_result}), 200

        elif role == "CourtRegistrar":

            registrar = (
                db.query(Courtregistrar)
                .filter_by(userid=current_user.userid)
                .first()
            )

            if not registrar:
                return jsonify({"cases": []}), 200

            cases = (
                db.query(Cases)
                .join(
                    t_courtaccess,
                    Cases.caseid == t_courtaccess.c.caseid,
                )
                .filter(
                    t_courtaccess.c.courtid == registrar.courtid
                )
                .all()
            )

            result = [_serialize_registrar_case(db, case) for case in cases]
            return jsonify({"cases": result}), 200

        else:

            cases = db.query(Cases).all()

        result = []

        for case in cases:

            result.append({
                "caseid": case.caseid,
                "title": case.title,
                "description": case.description,
                "casetype": case.casetype,
                "status": case.status,
                "filingdate": (
                    case.filingdate.isoformat()
                    if case.filingdate
                    else None
                ),
            })

        return jsonify({"cases": result}), 200

    except Exception as e:
        logging.error("Error in get_cases: %s", e, exc_info=True)
        return jsonify({"message": str(e)}), 500

    finally:

        db.close()


@cases_bp.route(
    '/cases/<int:case_id>/assign',
    methods=['POST']
)
@login_required
def assign_case(case_id):

    db = SessionLocal()

    try:

        data = request.get_json()

        lawyer_id = data.get("lawyerid")
        judge_id = data.get("judgeid")
        prosecutor_id = data.get("prosecutorid")

        case = db.query(Cases).get(case_id)

        if not case:
            return jsonify({
                "message":
                "Case not found"
            }), 404

        conn = get_pg_connection()

        try:

            cur = conn.cursor()

            # --------------------------------------
            # LAWYER
            # --------------------------------------
            if lawyer_id:

                cur.execute(
                    """
                    INSERT INTO caselawyeraccess
                    (
                        lawyerid,
                        caseid
                    )
                    VALUES (%s,%s)
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        lawyer_id,
                        case_id
                    )
                )

            # --------------------------------------
            # JUDGE
            # --------------------------------------
            if judge_id:

                cur.execute(
                    """
                    INSERT INTO judgeaccess
                    (
                        judgeid,
                        caseid
                    )
                    VALUES (%s,%s)
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        judge_id,
                        case_id
                    )
                )

            # --------------------------------------
            # PROSECUTOR
            # --------------------------------------
            if prosecutor_id:

                cur.execute(
                    """
                    INSERT INTO prosecutorassign
                    (
                        prosecutorid,
                        caseid
                    )
                    VALUES (%s,%s)
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        prosecutor_id,
                        case_id
                    )
                )

            conn.commit()

        finally:

            conn.close()

        return jsonify({
            "message":
            "Assignments completed successfully"
        })

    except Exception as e:

        return jsonify({
            "message": str(e)
        }), 500

    finally:

        db.close()

@cases_bp.route('/verifycases', methods=['POST'])
@login_required
def verify_case():
    """CourtRegistrar verifies a case: assigns case number, judge, prosecutor,
    optional respondent lawyer, and sets status to 'Open'."""

    if current_user.role != 'CourtRegistrar':
        return jsonify({'error': 'Only court registrars can verify cases'}), 403

    data = request.get_json() or {}
    caseid = data.get('caseid')
    judgename = (data.get('judgename') or '').strip()
    prosecutorname = (data.get('prosecutorname') or '').strip()
    respondent_lawyer_id = data.get('respondent_lawyer_id')

    if not caseid:
        return jsonify({'error': 'caseid is required'}), 400
    if not judgename:
        return jsonify({'error': 'Please select a judge'}), 400

    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Verify case exists
        cur.execute(
            "SELECT caseid, casenumber FROM cases WHERE caseid = %s",
            (caseid,)
        )
        case_row = cur.fetchone()
        if not case_row:
            return jsonify({'error': 'Case not found'}), 404

        # Generate case number if not already assigned
        casenumber = case_row['casenumber']
        if not casenumber:
            year = datetime.date.today().year
            casenumber = f"CASE-{year}-{int(caseid):04d}"

        # Update case: assign case number and set status to Open
        cur.execute(
            "UPDATE cases SET casenumber = %s, status = 'Open', "
            "updatedat = NOW() WHERE caseid = %s",
            (casenumber, caseid)
        )

        # Resolve and assign judge by full name
        name_parts = judgename.split()
        jfirst = name_parts[0]
        jlast = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        cur.execute(
            """
            SELECT j.judgeid FROM judge j
            JOIN users u ON u.userid = j.userid
            WHERE LOWER(u.firstname) = LOWER(%s)
              AND LOWER(u.lastname) = LOWER(%s)
            LIMIT 1
            """,
            (jfirst, jlast)
        )
        judge_row = cur.fetchone()
        if judge_row:
            cur.execute(
                "INSERT INTO judgeaccess (judgeid, caseid) "
                "VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (judge_row['judgeid'], caseid)
            )

        # Resolve and assign prosecutor by name (optional)
        if prosecutorname:
            cur.execute(
                "SELECT prosecutorid FROM prosecutor "
                "WHERE LOWER(name) = LOWER(%s) LIMIT 1",
                (prosecutorname,)
            )
            prosecutor_row = cur.fetchone()
            if prosecutor_row:
                cur.execute(
                    "INSERT INTO prosecutorassign (prosecutorid, caseid) "
                    "VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (prosecutor_row['prosecutorid'], caseid)
                )

        # Assign respondent / opposing lawyer (optional)
        if respondent_lawyer_id:
            try:
                rl_id = int(respondent_lawyer_id)
                cur.execute(
                    "SELECT 1 FROM information_schema.columns "
                    "WHERE table_name='caselawyeraccess' AND column_name='status'"
                )
                has_status = cur.fetchone() is not None

                if has_status:
                    cur.execute(
                        """
                        INSERT INTO caselawyeraccess
                            (caseid, lawyerid, side, is_lead, status)
                        VALUES (%s, %s, 'respondent', FALSE, 'approved')
                        ON CONFLICT (caseid, lawyerid) DO UPDATE
                        SET side = EXCLUDED.side, status = EXCLUDED.status
                        """,
                        (caseid, rl_id)
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO caselawyeraccess
                            (caseid, lawyerid, side, is_lead)
                        VALUES (%s, %s, 'respondent', FALSE)
                        ON CONFLICT (caseid, lawyerid) DO UPDATE
                        SET side = EXCLUDED.side
                        """,
                        (caseid, rl_id)
                    )
            except (ValueError, TypeError):
                pass

        conn.commit()

        from utils.logging import write_log
        write_log("UPDATE", f"Case verified and opened — case number: {casenumber}", "case")

        # In-app notifications
        try:
            from utils.notifications import push_notification
            # Notify the assigned judge
            if judge_row:
                cur.execute("SELECT userid FROM judge WHERE judgeid = %s", (judge_row['judgeid'],))
                jr = cur.fetchone()
                if jr:
                    push_notification(jr['userid'], "New Case Assigned",
                        f"You have been assigned as judge on case {casenumber}.", "info", caseid)
            # Notify all lawyers already on the case
            cur.execute(
                "SELECT l.userid FROM lawyer l JOIN caselawyeraccess cla ON cla.lawyerid = l.lawyerid WHERE cla.caseid = %s",
                (caseid,)
            )
            for lrow in cur.fetchall():
                push_notification(lrow['userid'], "Case Verified",
                    f"Your case {casenumber} has been verified and is now Open.", "success", caseid)
        except Exception:
            pass

        return jsonify({
            'message': 'Case verified successfully',
            'casenumber': casenumber,
            'caseid': caseid,
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        if conn:
            conn.close()


@cases_bp.route('/cases/<int:case_id>/history', methods=['GET'])
@login_required
def get_case_history(case_id):
    """
    Return a full chronological timeline for one case.
    Merges auto-generated events (derived from existing DB records) with
    manual casehistory entries so the view always shows something meaningful.
    """
    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # ── base case info + person names ──────────────────────────────────
        cur.execute(
            """
            SELECT
                c.caseid, c.title, c.casenumber, c.status,
                c.filingdate, c.casetype,
                (
                    SELECT TRIM(u.firstname || ' ' || u.lastname)
                    FROM judgeaccess ja
                    JOIN judge j  ON j.judgeid  = ja.judgeid
                    JOIN users u  ON u.userid   = j.userid
                    WHERE ja.caseid = c.caseid LIMIT 1
                ) AS judgename,
                (
                    SELECT TRIM(u.firstname || ' ' || u.lastname)
                    FROM caselawyeraccess cla
                    JOIN lawyer lw ON lw.lawyerid = cla.lawyerid
                    JOIN users u   ON u.userid    = lw.userid
                    WHERE cla.caseid = c.caseid LIMIT 1
                ) AS lawyername,
                (
                    SELECT TRIM(u.firstname || ' ' || u.lastname)
                    FROM caseparticipantaccess cpa
                    JOIN caseparticipant cp ON cp.participantid = cpa.participantid
                    JOIN users u            ON u.userid         = cp.userid
                    WHERE cpa.caseid = c.caseid LIMIT 1
                ) AS clientname,
                (
                    SELECT p.name
                    FROM prosecutorassign pa
                    JOIN prosecutor p ON p.prosecutorid = pa.prosecutorid
                    WHERE pa.caseid = c.caseid LIMIT 1
                ) AS prosecutorname
            FROM cases c
            WHERE c.caseid = %s
            """,
            (case_id,),
        )
        case = cur.fetchone()
        if not case:
            return jsonify({"error": "Case not found"}), 404

        # ── helper ─────────────────────────────────────────────────────────
        def ev(action, remarks="", date=None, status=None, eid=None, etype="auto", sort_offset=0):
            """Build one timeline entry dict."""
            d_str = date.isoformat() if date else None
            # sort key: (date_str or filing fallback, offset within same date)
            sk = (d_str or (case["filingdate"].isoformat() if case["filingdate"] else "0000-00-00"), sort_offset)
            return {
                "historyid":  eid,
                "caseName":   case["title"],
                "casenumber": case["casenumber"] or "—",
                "judgeName":  case["judgename"]  or "—",
                "clientName": case["clientname"] or "—",
                "lawyerName": case["lawyername"] or "—",
                "actionDate": d_str,
                "actionTaken": action,
                "remarks":    remarks,
                "status":     status or case["status"],
                "eventType":  etype,
                "_sort_key":  sk,
            }

        events = []

        # 1. Case filed
        if case["filingdate"]:
            events.append(ev(
                f"Case filed — type: {case['casetype'] or 'N/A'}",
                remarks="Case registered in the system.",
                date=case["filingdate"],
                status="Pending",
                sort_offset=0,
            ))

        # 2. Case verified / opened by registrar
        if case["casenumber"] and case["status"] in ("Open", "Closed"):
            events.append(ev(
                f"Case verified and opened by Court Registrar"
                f" — assigned case number {case['casenumber']}",
                date=case["filingdate"],   # best proxy available
                status="Open",
                sort_offset=1,
            ))

        # 3. Judge assigned
        if case["judgename"]:
            events.append(ev(
                f"Judge assigned: {case['judgename']}",
                date=case["filingdate"],
                sort_offset=2,
            ))

        # 4. Prosecutor assigned
        if case["prosecutorname"]:
            events.append(ev(
                f"Prosecutor assigned: {case['prosecutorname']}",
                date=case["filingdate"],
                sort_offset=3,
            ))

        # 5. Hearings
        cur.execute(
            """
            SELECT hearingdate, hearingstatus
            FROM hearings
            WHERE caseid = %s
            ORDER BY hearingdate ASC
            """,
            (case_id,),
        )
        for h in cur.fetchall():
            label = (
                f"Hearing — outcome: {h['hearingstatus']}"
                if h["hearingstatus"] and h["hearingstatus"] != "scheduled"
                else "Hearing scheduled"
            )
            events.append(ev(label, date=h["hearingdate"], sort_offset=10))

        # 6. Bail
        cur.execute(
            "SELECT baildate, bailstatus, bailamount FROM bail WHERE caseid = %s",
            (case_id,),
        )
        bail = cur.fetchone()
        if bail and bail["baildate"]:
            events.append(ev(
                f"Bail application filed"
                f" — amount: {bail['bailamount'] or 'N/A'}"
                f", status: {bail['bailstatus'] or 'N/A'}",
                date=bail["baildate"],
                sort_offset=10,
            ))

        # 7. Appeals
        cur.execute(
            """
            SELECT appealdate, decisiondate, appealstatus, decision
            FROM appeals WHERE caseid = %s ORDER BY appealdate ASC
            """,
            (case_id,),
        )
        for ap in cur.fetchall():
            if ap["appealdate"]:
                events.append(ev("Appeal filed", date=ap["appealdate"], sort_offset=10))
            if ap["decisiondate"] and ap["decision"]:
                events.append(ev(
                    f"Appeal decision: {ap['decision']}",
                    date=ap["decisiondate"],
                    status=ap["appealstatus"] or case["status"],
                    sort_offset=10,
                ))

        # 8. Final decision
        cur.execute(
            """
            SELECT decisiondate, verdict, decisionsummary
            FROM finaldecision WHERE caseid = %s
            ORDER BY decisiondate DESC LIMIT 1
            """,
            (case_id,),
        )
        fd = cur.fetchone()
        if fd and fd["decisiondate"]:
            events.append(ev(
                f"Final verdict: {fd['verdict']}",
                remarks=fd["decisionsummary"] or "",
                date=fd["decisiondate"],
                status="Closed",
                sort_offset=20,
            ))

        # 9. Manual notes from casehistory table
        cur.execute(
            """
            SELECT historyid, actiondate, actiontaken, remarks
            FROM casehistory WHERE caseid = %s
            ORDER BY actiondate ASC NULLS LAST
            """,
            (case_id,),
        )
        for row in cur.fetchall():
            events.append(ev(
                row["actiontaken"] or "",
                remarks=row["remarks"] or "",
                date=row["actiondate"],
                eid=row["historyid"],
                etype="manual",
                sort_offset=5,
            ))

        # ── sort chronologically, remove internal key ──────────────────────
        events.sort(key=lambda e: e["_sort_key"])
        for e in events:
            del e["_sort_key"]

        return jsonify({"history": events}), 200

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if conn:
            conn.close()

