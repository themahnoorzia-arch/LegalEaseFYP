#!/usr/bin/env python3
"""
Rich demo data for LegalEase — populates relationships across all modules.

Run from backend folder (after base users/court exist):
    python seed_demo_data.py

Or: python seed_database.py  (calls this at the end)

Password for all accounts: LegalEase2025!
"""
from datetime import date, time, timedelta
from decimal import Decimal

from sqlalchemy import text
from werkzeug.security import generate_password_hash

from db.db import SessionLocal

DEFAULT_PASSWORD = "LegalEase2025!"


def _get_or_create_user(db, role, fn, ln, email, phone, cnic, dob, pw_hash):
    row = db.execute(
        text("SELECT userid FROM users WHERE email = :email"),
        {"email": email},
    ).fetchone()
    if row:
        uid = row[0]
        db.execute(
            text(
                "UPDATE users SET firstname=:fn, lastname=:ln, role=:role, "
                "phoneno=:phone, cnic=:cnic, dob=:dob, password=:pw WHERE userid=:uid"
            ),
            {"fn": fn, "ln": ln, "role": role, "phone": phone, "cnic": cnic, "dob": dob, "pw": pw_hash, "uid": uid},
        )
    else:
        uid = db.execute(
            text(
                "INSERT INTO users (role, firstname, lastname, email, phoneno, cnic, dob, password) "
                "VALUES (:role, :fn, :ln, :email, :phone, :cnic, :dob, :pw) RETURNING userid"
            ),
            {"role": role, "fn": fn, "ln": ln, "email": email, "phone": phone, "cnic": cnic, "dob": dob, "pw": pw_hash},
        ).fetchone()[0]
    return uid


def _upsert_case(db, title, description, casetype, status, filingdate, casenumber=None):
    row = db.execute(
        text("SELECT caseid FROM cases WHERE title = :t ORDER BY caseid LIMIT 1"),
        {"t": title},
    ).fetchone()
    if row:
        cid = row[0]
        db.execute(
            text(
                "UPDATE cases SET description=:d, casetype=:ct, status=:s, "
                "filingdate=:f, casenumber=COALESCE(:cn, casenumber) WHERE caseid=:id"
            ),
            {"d": description, "ct": casetype, "s": status, "f": filingdate, "cn": casenumber, "id": cid},
        )
    else:
        cid = db.execute(
            text(
                "INSERT INTO cases (title, description, casetype, status, filingdate, casenumber) "
                "VALUES (:t, :d, :ct, :s, :f, :cn) RETURNING caseid"
            ),
            {"t": title, "d": description, "ct": casetype, "s": status, "f": filingdate, "cn": casenumber},
        ).fetchone()[0]
    return cid


def _link_case_court(db, court_id, case_id):
    db.execute(
        text("INSERT INTO courtaccess (courtid, caseid) VALUES (:c, :case) ON CONFLICT DO NOTHING"),
        {"c": court_id, "case": case_id},
    )


def _link_lawyer(db, case_id, lawyer_id, side, status="approved", is_lead=True):
    db.execute(
        text(
            """
            INSERT INTO caselawyeraccess (caseid, lawyerid, side, is_lead, status)
            VALUES (:case, :lawyer, :side, :lead, :status)
            ON CONFLICT (caseid, lawyerid) DO UPDATE
            SET side = EXCLUDED.side, status = EXCLUDED.status, is_lead = EXCLUDED.is_lead
            """
        ),
        {"case": case_id, "lawyer": lawyer_id, "side": side, "lead": is_lead, "status": status},
    )


def _link_participant(db, case_id, participant_id):
    db.execute(
        text(
            "INSERT INTO caseparticipantaccess (participantid, caseid) "
            "VALUES (:p, :case) ON CONFLICT DO NOTHING"
        ),
        {"p": participant_id, "case": case_id},
    )


def _link_judge(db, case_id, judge_id):
    db.execute(
        text("INSERT INTO judgeaccess (caseid, judgeid) VALUES (:case, :j) ON CONFLICT DO NOTHING"),
        {"case": case_id, "j": judge_id},
    )


def _add_history(db, case_id, action, remarks, action_date=None):
    exists = db.execute(
        text(
            "SELECT 1 FROM casehistory WHERE caseid=:c AND actiontaken=:a AND remarks=:r LIMIT 1"
        ),
        {"c": case_id, "a": action, "r": remarks},
    ).fetchone()
    if exists:
        return
    db.execute(
        text(
            "INSERT INTO casehistory (caseid, actiondate, actiontaken, remarks) "
            "VALUES (:c, :d, :a, :r)"
        ),
        {"c": case_id, "d": action_date or date.today(), "a": action, "r": remarks},
    )


def _add_document(db, case_id, title, doc_type, filepath):
    existing = db.execute(
        text(
            "SELECT d.documentid FROM documents d "
            "JOIN documentcase dc ON dc.documentid = d.documentid "
            "WHERE dc.caseid = :c AND d.documenttitle = :t LIMIT 1"
        ),
        {"c": case_id, "t": title},
    ).fetchone()
    if existing:
        return existing[0]
    doc_id = db.execute(
        text(
            "INSERT INTO documents (documenttitle, documenttype, uploaddate, filepath) "
            "VALUES (:title, :type, :ud, :path) RETURNING documentid"
        ),
        {"title": title, "type": doc_type, "ud": date.today(), "path": filepath},
    ).fetchone()[0]
    db.execute(
        text(
            "INSERT INTO documentcase (caseid, documentid, submissiondate) "
            "VALUES (:c, :d, :sd) ON CONFLICT DO NOTHING"
        ),
        {"c": case_id, "d": doc_id, "sd": date.today()},
    )
    return doc_id


def run():
    pw_hash = generate_password_hash(DEFAULT_PASSWORD)
    db = SessionLocal()

    try:
        print("Seeding comprehensive demo data...")

        # ── Users ──────────────────────────────────────────────
        client_zaina = _get_or_create_user(
            db, "CaseParticipant", "Zaina", "Zia", "client@gmail.com",
            "03001234567", "35202-1234567-8", "1998-05-15", pw_hash,
        )
        client_ali = _get_or_create_user(
            db, "CaseParticipant", "Ali", "Raza", "ali.raza@client.com",
            "03006666666", "35202-6666666-6", "1995-04-20", pw_hash,
        )
        ahmed_uid = _get_or_create_user(
            db, "Lawyer", "Ahmed", "Khan", "ahmed.khan@legalease.com",
            "03001111111", "35202-1111111-1", "1990-03-12", pw_hash,
        )
        sara_uid = _get_or_create_user(
            db, "Lawyer", "Sara", "Malik", "sara.malik@legalease.com",
            "03002222222", "35202-2222222-2", "1992-07-22", pw_hash,
        )
        omar_uid = _get_or_create_user(
            db, "Lawyer", "Omar", "Hassan", "omar.hassan@legalease.com",
            "03003333333", "35202-3333333-3", "1988-11-01", pw_hash,
        )
        judge_uid = _get_or_create_user(
            db, "Judge", "Test", "Judge", "test@judge.com",
            "03004444444", "35202-4444444-4", "1975-01-20", pw_hash,
        )
        reg_uid = _get_or_create_user(
            db, "CourtRegistrar", "Fatima", "Registrar", "registrar@legalease.com",
            "03005555555", "35202-5555555-5", "1985-09-09", pw_hash,
        )

        # ── Court ──────────────────────────────────────────────
        court_row = db.execute(text("SELECT courtid FROM court WHERE courtname = 'Lahore District Court' LIMIT 1")).fetchone()
        if not court_row:
            court_id = db.execute(
                text(
                    "INSERT INTO court (courtname, type, location) "
                    "VALUES ('Lahore District Court', 'District', 'Fane Road, Lahore') RETURNING courtid"
                )
            ).fetchone()[0]
        else:
            court_id = court_row[0]

        db.execute(text("DELETE FROM courtregistrar WHERE userid = :u"), {"u": reg_uid})
        db.execute(
            text("INSERT INTO courtregistrar (userid, courtid, position) VALUES (:u, :c, :p)"),
            {"u": reg_uid, "c": court_id, "p": "Senior Registrar"},
        )

        # ── Profiles ───────────────────────────────────────────
        for uid, bar, spec, exp in [
            (ahmed_uid, 100001, "Criminal Law", 8),
            (sara_uid, 100002, "Family Law", 5),
            (omar_uid, 100003, "Corporate Law", 12),
        ]:
            db.execute(text("DELETE FROM lawyer WHERE userid = :u"), {"u": uid})
            db.execute(
                text(
                    "INSERT INTO lawyer (barlicenseno, userid, specialization, experienceyears) "
                    "VALUES (:bar, :u, :spec, :exp)"
                ),
                {"bar": bar, "u": uid, "spec": spec, "exp": exp},
            )

        lawyer_ahmed = db.execute(text("SELECT lawyerid FROM lawyer WHERE userid=:u"), {"u": ahmed_uid}).fetchone()[0]
        lawyer_sara = db.execute(text("SELECT lawyerid FROM lawyer WHERE userid=:u"), {"u": sara_uid}).fetchone()[0]
        lawyer_omar = db.execute(text("SELECT lawyerid FROM lawyer WHERE userid=:u"), {"u": omar_uid}).fetchone()[0]

        db.execute(text("DELETE FROM judge WHERE userid = :u"), {"u": judge_uid})
        db.execute(
            text(
                "INSERT INTO judge (userid, position, specialization, expyears, appointmentdate) "
                "VALUES (:u, :pos, :spec, :exp, :ad)"
            ),
            {"u": judge_uid, "pos": "District & Sessions Judge", "spec": "Criminal Law", "exp": 15, "ad": date(2010, 1, 15)},
        )
        judge_id = db.execute(text("SELECT judgeid FROM judge WHERE userid=:u"), {"u": judge_uid}).fetchone()[0]
        db.execute(
            text("INSERT INTO judgeworksin (judgeid, courtid) VALUES (:j, :c) ON CONFLICT DO NOTHING"),
            {"j": judge_id, "c": court_id},
        )

        def participant_for(uid, address):
            db.execute(text("DELETE FROM caseparticipant WHERE userid = :u"), {"u": uid})
            db.execute(
                text("INSERT INTO caseparticipant (userid, address) VALUES (:u, :a) RETURNING participantid"),
                {"u": uid, "a": address},
            )
            return db.execute(text("SELECT participantid FROM caseparticipant WHERE userid=:u"), {"u": uid}).fetchone()[0]

        part_zaina = participant_for(client_zaina, "House 12, Gulberg III, Lahore")
        part_ali = participant_for(client_ali, "45 Model Town, Lahore")

        # ── Courtrooms ─────────────────────────────────────────
        for room_no, cap, avail in [(1, 80, "Available"), (2, 50, "Available"), (3, 30, "In Use")]:
            db.execute(
                text(
                    """
                    INSERT INTO courtroom (courtid, courtroomid, courtroomno, capacity, availability)
                    VALUES (:c, :rid, :no, :cap, :av)
                    ON CONFLICT (courtid, courtroomid) DO UPDATE
                    SET courtroomno=EXCLUDED.courtroomno, capacity=EXCLUDED.capacity,
                        availability=EXCLUDED.availability
                    """
                ),
                {"c": court_id, "rid": room_no, "no": room_no, "cap": cap, "av": avail},
            )

        # ── Prosecutors ────────────────────────────────────────
        prosecutors = []
        for name, exp in [("Asad Mehmood", 7), ("Hina Shah", 4), ("Bilal Qureshi", 10)]:
            row = db.execute(text("SELECT prosecutorid FROM prosecutor WHERE name=:n"), {"n": name}).fetchone()
            if row:
                pid = row[0]
            else:
                pid = db.execute(
                    text("INSERT INTO prosecutor (name, experience, status) VALUES (:n, :e, 'Active') RETURNING prosecutorid"),
                    {"n": name, "e": exp},
                ).fetchone()[0]
            prosecutors.append(pid)

        # ── Cases (canonical demo set) ─────────────────────────
        case_criminal = _upsert_case(
            db, "State v. Ali Raza",
            "Theft and possession of stolen property under PPC 379/411",
            "Criminal", "Open", date(2024, 6, 1), "LDC-2024-0001",
        )
        case_family = _upsert_case(
            db, "Khan Family Custody Dispute",
            "Child custody and visitation rights for minor aged 8",
            "Family", "Pending", date(2024, 8, 15), None,
        )
        case_corporate = _upsert_case(
            db, "TechCorp Contract Breach",
            "Breach of software licensing agreement — damages claimed PKR 5M",
            "Corporate", "Open", date(2025, 1, 10), "LDC-2025-0001",
        )

        cases = {
            "criminal": case_criminal,
            "family": case_family,
            "corporate": case_corporate,
        }

        for cid in cases.values():
            _link_case_court(db, court_id, cid)
            _link_judge(db, cid, judge_id)

        # Lawyer ↔ case relationships
        _link_lawyer(db, case_criminal, lawyer_ahmed, "petitioner", "approved", True)
        _link_lawyer(db, case_criminal, lawyer_omar, "respondent", "pending", False)  # join request demo
        _link_lawyer(db, case_family, lawyer_sara, "petitioner", "approved", True)
        _link_lawyer(db, case_corporate, lawyer_omar, "petitioner", "approved", True)
        _link_lawyer(db, case_corporate, lawyer_ahmed, "respondent", "approved", False)

        # Client ↔ case
        _link_participant(db, case_criminal, part_ali)
        _link_participant(db, case_family, part_zaina)
        _link_participant(db, case_corporate, part_zaina)

        # Prosecutor on criminal case
        db.execute(
            text("INSERT INTO prosecutorassign (prosecutorid, caseid) VALUES (:p, :c) ON CONFLICT DO NOTHING"),
            {"p": prosecutors[0], "c": case_criminal},
        )

        # ── Case history (shows registrar workflow) ────────────
        history_entries = [
            (case_criminal, "Case filing requested by lawyer", "Criminal complaint filed by prosecution", date(2024, 6, 1)),
            (case_criminal, "Case verified by registrar", "Assigned case number: LDC-2024-0001", date(2024, 6, 3)),
            (case_criminal, "First hearing scheduled", "Initial appearance in Courtroom 1", date(2024, 6, 10)),
            (case_family, "Case filing requested by lawyer", "Filed as Family case for client Zaina Zia", date(2024, 8, 15)),
            (case_corporate, "Case verified by registrar", "Assigned case number: LDC-2025-0001", date(2025, 1, 12)),
            (case_corporate, "Discovery phase opened", "Both parties exchanged document lists", date(2025, 2, 1)),
        ]
        for cid, action, remarks, adate in history_entries:
            _add_history(db, cid, action, remarks, adate)

        # ── Hearings ───────────────────────────────────────────
        next_hid = db.execute(text("SELECT COALESCE(MAX(hearingid), 0) + 1 FROM hearings")).fetchone()[0]
        hearings = [
            (case_criminal, date(2026, 6, 20), time(9, 30), "Courtroom 1", "Arraignment hearing", "scheduled"),
            (case_criminal, date(2026, 7, 15), time(11, 0), "Courtroom 1", "Evidence presentation", "scheduled"),
            (case_family, date(2026, 6, 25), time(10, 0), "Courtroom 2", "Mediation session", "scheduled"),
            (case_corporate, date(2026, 6, 18), time(14, 0), "Courtroom 3", "Pre-trial conference", "completed"),
        ]
        for case_id, hdate, htime, venue, remarks, hstatus in hearings:
            db.execute(
                text(
                    """
                    INSERT INTO hearings (caseid, hearingid, judgeid, hearingdate, hearingtime, venue, remarks, hearingstatus)
                    VALUES (:case, :hid, :j, :hd, :ht, :v, :rm, :st)
                    ON CONFLICT (caseid, hearingid) DO NOTHING
                    """
                ),
                {"case": case_id, "hid": next_hid, "j": judge_id, "hd": hdate, "ht": htime, "v": venue, "rm": remarks, "st": hstatus},
            )
            next_hid += 1

        # ── Documents (linked to cases → visible to lawyers) ─────
        docs = [
            (case_criminal, "FIR Copy - State v Ali Raza.pdf", "Filing", "/uploads/demo/fir_ali_raza.pdf"),
            (case_criminal, "Police Investigation Report.pdf", "Evidence", "/uploads/demo/police_report.pdf"),
            (case_criminal, "Bail Application Draft.docx", "Motion", "/uploads/demo/bail_app.docx"),
            (case_family, "Custody Petition.pdf", "Filing", "/uploads/demo/custody_petition.pdf"),
            (case_family, "Child Welfare Report.pdf", "Report", "/uploads/demo/welfare_report.pdf"),
            (case_corporate, "Software License Agreement.pdf", "Contract", "/uploads/demo/license_agreement.pdf"),
            (case_corporate, "Breach Notice Letter.pdf", "Correspondence", "/uploads/demo/breach_notice.pdf"),
            (case_corporate, "Financial Damages Summary.xlsx", "Financial", "/uploads/demo/damages.xlsx"),
        ]
        for cid, title, dtype, path in docs:
            _add_document(db, cid, title, dtype, path)

        # ── Evidence ───────────────────────────────────────────
        evidence_items = [
            (case_criminal, "Physical", "Recovered mobile phone from accused", "/uploads/demo/evidence_phone.jpg"),
            (case_criminal, "Documentary", "Shop CCTV still frames", "/uploads/demo/evidence_cctv.pdf"),
            (case_corporate, "Digital", "Email chain showing license violation", "/uploads/demo/evidence_emails.pdf"),
        ]
        for case_id, etype, desc, path in evidence_items:
            exists = db.execute(
                text("SELECT 1 FROM evidence WHERE caseid=:c AND description=:d LIMIT 1"),
                {"c": case_id, "d": desc},
            ).fetchone()
            if not exists:
                db.execute(
                    text(
                        "INSERT INTO evidence (caseid, evidencetype, description, submitteddate, filepath) "
                        "VALUES (:c, :t, :d, :sd, :p)"
                    ),
                    {"c": case_id, "t": etype, "d": desc, "sd": date.today(), "p": path},
                )

        # ── Witnesses ──────────────────────────────────────────
        witnesses = []
        for fn, ln, cnic, phone in [
            ("Hamza", "Siddiqui", "3520212345678", "03007777777"),
            ("Ayesha", "Tariq", "3520298765432", "03008888888"),
        ]:
            row = db.execute(text("SELECT witnessid FROM witnesses WHERE cnic=:c"), {"c": cnic}).fetchone()
            if row:
                wid = row[0]
            else:
                wid = db.execute(
                    text(
                        "INSERT INTO witnesses (firstname, lastname, cnic, phone, email, address) "
                        "VALUES (:fn, :ln, :c, :p, :e, :a) RETURNING witnessid"
                    ),
                    {"fn": fn, "ln": ln, "c": cnic, "p": phone, "e": f"{fn.lower()}@witness.com", "a": "Lahore"},
                ).fetchone()[0]
            witnesses.append(wid)

        db.execute(
            text(
                "INSERT INTO witnesscase (caseid, witnessid, statement, statementdate) "
                "VALUES (:c, :w, :s, :d) ON CONFLICT DO NOTHING"
            ),
            {"c": case_criminal, "w": witnesses[0], "s": "Saw accused near shop on night of incident", "d": date(2024, 6, 5)},
        )
        db.execute(
            text(
                "INSERT INTO witnesscase (caseid, witnessid, statement, statementdate) "
                "VALUES (:c, :w, :s, :d) ON CONFLICT DO NOTHING"
            ),
            {"c": case_family, "w": witnesses[1], "s": "Neighbor testimony regarding child living conditions", "d": date(2024, 9, 1)},
        )

        # ── Remands (criminal case) ────────────────────────────
        remand_exists = db.execute(text("SELECT 1 FROM remands WHERE caseid=:c LIMIT 1"), {"c": case_criminal}).fetchone()
        if not remand_exists:
            db.execute(
                text(
                    """
                    INSERT INTO remands (caseid, remandid, startdate, enddate, remandtype, remandreason, status)
                    VALUES (:c, 1, :sd, :ed, 'Police', 'Further investigation required', 'Completed')
                    """
                ),
                {"c": case_criminal, "sd": date(2024, 6, 2), "ed": date(2024, 6, 9)},
            )

        # ── Surety + Bail ──────────────────────────────────────
        surety_row = db.execute(text("SELECT suretyid FROM surety WHERE cnic='3520255555555' LIMIT 1")).fetchone()
        if not surety_row:
            surety_id = db.execute(
                text(
                    "INSERT INTO surety (cnic, phone, firstname, lastname, email, address, pasthistory) "
                    "VALUES ('3520255555555', '03009999999', 'Kamran', 'Butt', 'kamran@surety.com', "
                    "'DHA Phase 5, Lahore', 'No prior defaults') RETURNING suretyid"
                )
            ).fetchone()[0]
        else:
            surety_id = surety_row[0]

        bail_exists = db.execute(text("SELECT 1 FROM bail WHERE caseid=:c LIMIT 1"), {"c": case_criminal}).fetchone()
        if not bail_exists:
            db.execute(
                text(
                    """
                    INSERT INTO bail (caseid, bailid, suretyid, bailstatus, bailamount, baildate, remarks, bailcondition)
                    VALUES (:c, 1, :s, 'Granted', 200000, :bd, 'Bail granted with surety',
                            'Accused shall not leave district without permission')
                    """
                ),
                {"c": case_criminal, "s": surety_id, "bd": date(2024, 6, 12)},
            )

        # ── Payments ───────────────────────────────────────────
        payments = [
            (case_criminal, lawyer_ahmed, "Court Fee", "Filing fee for criminal case", Decimal("5000"), "Paid", "Cash"),
            (case_family, lawyer_sara, "Court Fee", "Custody petition filing", Decimal("3000"), "Pending", "Online Transfer"),
            (case_corporate, lawyer_omar, "Legal Fee", "Corporate counsel retainer", Decimal("25000"), "Paid", "Online Transfer"),
        ]
        for case_id, lawyer_id, ptype, purpose, amount, status, mode in payments:
            exists = db.execute(
                text("SELECT 1 FROM payments WHERE caseid=:c AND purpose=:p LIMIT 1"),
                {"c": case_id, "p": purpose},
            ).fetchone()
            if exists:
                continue
            db.execute(
                text(
                    """
                    INSERT INTO payments (mode, lawyerid, courtid, caseid, paymenttype, balance, purpose, paymentdate, status)
                    VALUES (:mode, :lawyer, :court, :case, :ptype, :bal, :purpose, :pd, :status)
                    """
                ),
                {
                    "mode": mode, "lawyer": lawyer_id, "court": court_id, "case": case_id,
                    "ptype": ptype, "bal": amount, "purpose": purpose,
                    "pd": date.today(), "status": status,
                },
            )

        # ── Appeals ──────────────────────────────────────────────
        appeal_exists = db.execute(text("SELECT 1 FROM appeals WHERE caseid=:c LIMIT 1"), {"c": case_corporate}).fetchone()
        if not appeal_exists:
            next_aid = db.execute(text("SELECT COALESCE(MAX(appealid), 0) + 1 FROM appeals")).fetchone()[0]
            db.execute(
                text(
                    """
                    INSERT INTO appeals (caseid, appealid, appealdate, appealstatus, decisiondate, decision)
                    VALUES (:c, :a, :ad, :st, NULL, NULL)
                    """
                ),
                {"c": case_corporate, "a": next_aid, "ad": date(2025, 3, 1), "st": "Pending"},
            )

        db.commit()

        print("=" * 60)
        print("Demo data seeded successfully!")
        print(f"Password for ALL accounts: {DEFAULT_PASSWORD}")
        print("=" * 60)
        print("\nHow things connect:")
        print("  Criminal case  - Ahmed Khan (defense) + Omar Hassan (pending join)")
        print("                   - Ali Raza (client), Prosecutor Asad Mehmood")
        print("                   - Bail, remand, evidence, witnesses, 3 documents")
        print("  Family case    - Sara Malik (lawyer), Zaina Zia (client), PENDING verify")
        print("  Corporate case - Omar Hassan vs Ahmed Khan, appeal pending")
        print("\nLogin accounts:")
        for label, email in [
            ("Client (Zaina)", "client@gmail.com"),
            ("Client (Ali Raza)", "ali.raza@client.com"),
            ("Lawyer Ahmed", "ahmed.khan@legalease.com"),
            ("Lawyer Sara", "sara.malik@legalease.com"),
            ("Lawyer Omar", "omar.hassan@legalease.com"),
            ("Judge", "test@judge.com"),
            ("Registrar", "registrar@legalease.com"),
        ]:
            print(f"  {label:20} {email}")
        print()

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
