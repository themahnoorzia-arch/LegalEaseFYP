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
        side = data.get('side', '').strip()
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

        # Attempt to detect likely duplicate by casenumber or matching participant name
        casenumber_param = casenumber or ''
        cur.execute(
            """
            SELECT c.caseid
            FROM cases c
            LEFT JOIN caseparticipantaccess cpa ON cpa.caseid = c.caseid
            LEFT JOIN caseparticipant cp ON cp.participantid = cpa.participantid
            LEFT JOIN users u ON u.userid = cp.userid
            WHERE (c.casenumber = %s AND %s <> '')
               OR (similarity(CONCAT_WS(' ', u.firstname, u.lastname), %s) > 0.6)
            GROUP BY c.caseid
            LIMIT 1
            """,
            (casenumber_param, casenumber_param, fullname),
        )

        duplicate_case = cur.fetchone()
        if duplicate_case:
            caseid = duplicate_case['caseid']
            cur.execute(
                "SELECT lawyerid FROM lawyer WHERE userid = %s",
                (current_user.userid,)
            )
            lawyer_row = cur.fetchone()
            if not lawyer_row:
                return jsonify({'message': 'Lawyer profile not found'}), 404

            lawyerid = lawyer_row['lawyerid']
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
            return jsonify({
                'message': 'Joined existing case',
                'case_id': caseid
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
            WHERE firstname=%s
            AND lastname=%s
            """,
            (
                firstname,
                lastname
            )
        )

        user_row = cur.fetchone()

        if not user_row:
            return jsonify({
                'message':
                'User not found'
            }), 404

        # RealDictCursor returns a dict
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
            return jsonify({
                'message':
                'Participant not found'
            }), 404

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

        conn.commit()

        return jsonify({
            'message':
            'Case created successfully',
            'case_id':
            caseid
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
    side = (data.get('side') or '').strip()

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
            """
            INSERT INTO caselawyeraccess (caseid, lawyerid, side, is_lead, status)
            VALUES (%s, %s, %s, TRUE, 'pending')
            ON CONFLICT (caseid, lawyerid) DO UPDATE
            SET side = EXCLUDED.side, status = EXCLUDED.status
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

@cases_bp.route(
    '/cases/<int:case_id>/history',
    methods=['GET']
)
@login_required
def get_case_history(case_id):

    db = SessionLocal()

    try:

        history = (
            db.query(Casehistory)
            .filter_by(caseid=case_id)
            .order_by(Casehistory.actiondate.desc())
            .all()
        )

        result = []

        for item in history:
            result.append({
                "historyid": item.historyid,
                "date": (
                    item.actiondate.isoformat() if item.actiondate else None
                ),
                "event": item.actiontaken,
                "actiontaken": item.actiontaken,
                "remarks": item.remarks,
            })

        return jsonify({"history": result}), 200

    finally:

        db.close()

