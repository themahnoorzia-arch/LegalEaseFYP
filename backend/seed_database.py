#!/usr/bin/env python3
"""
Populate the database with demo data and set ONE password for all users.

Run from backend folder:
    python seed_database.py

Default login password for every account: LegalEase2025!
"""
from datetime import date, time, datetime

from sqlalchemy import text
from werkzeug.security import generate_password_hash

from db.db import SessionLocal, engine
from models import Base

DEFAULT_PASSWORD = "LegalEase2025!"


def run():
    pw_hash = generate_password_hash(DEFAULT_PASSWORD)
    db = SessionLocal()

    try:
        db.execute(
            text(
                "SELECT setval(pg_get_serial_sequence('users', 'userid'), "
                "COALESCE((SELECT MAX(userid) FROM users), 0))"
            )
        )

        users_spec = [
            ("Admin", "Mahnoor", "Zia", "admin@legalease.com", "03446077001", "34601-1321677-4", "2000-02-08"),
            ("CaseParticipant", "Zaina", "Zia", "client@gmail.com", "03001234567", "35202-1234567-8", "1998-05-15"),
            ("Lawyer", "Ahmed", "Khan", "ahmed.khan@legalease.com", "03001111111", "35202-1111111-1", "1990-03-12"),
            ("Lawyer", "Sara", "Malik", "sara.malik@legalease.com", "03002222222", "35202-2222222-2", "1992-07-22"),
            ("Lawyer", "Omar", "Hassan", "omar.hassan@legalease.com", "03003333333", "35202-3333333-3", "1988-11-01"),
            ("Judge", "Test", "Judge", "test@judge.com", "03004444444", "35202-4444444-4", "1975-01-20"),
            ("CourtRegistrar", "Fatima", "Registrar", "registrar@legalease.com", "03005555555", "35202-5555555-5", "1985-09-09"),
        ]

        user_ids = {}
        for role, fn, ln, email, phone, cnic, dob in users_spec:
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
                    {
                        "fn": fn, "ln": ln, "role": role, "phone": phone,
                        "cnic": cnic, "dob": dob, "pw": pw_hash, "uid": uid,
                    },
                )
            else:
                uid = db.execute(
                    text(
                        "INSERT INTO users (role, firstname, lastname, email, phoneno, cnic, dob, password) "
                        "VALUES (:role, :fn, :ln, :email, :phone, :cnic, :dob, :pw) RETURNING userid"
                    ),
                    {
                        "role": role, "fn": fn, "ln": ln, "email": email,
                        "phone": phone, "cnic": cnic, "dob": dob, "pw": pw_hash,
                    },
                ).fetchone()[0]
            user_ids[email] = uid

        # Profiles
        admin_uid = user_ids["admin@legalease.com"]
        db.execute(text("DELETE FROM admin WHERE userid = :u"), {"u": admin_uid})
        db.execute(text("INSERT INTO admin (userid) VALUES (:u) ON CONFLICT DO NOTHING"), {"u": admin_uid})

        client_uid = user_ids["client@gmail.com"]
        db.execute(text("DELETE FROM caseparticipant WHERE userid = :u"), {"u": client_uid})
        db.execute(
            text("INSERT INTO caseparticipant (userid, address) VALUES (:u, :a)"),
            {"u": client_uid, "a": "House 12, Gulberg III, Lahore"},
        )
        participant_id = db.execute(
            text("SELECT participantid FROM caseparticipant WHERE userid = :u"),
            {"u": client_uid},
        ).fetchone()[0]

        lawyers = []
        for email, bar, spec, exp in [
            ("ahmed.khan@legalease.com", 100001, "Criminal Law", 8),
            ("sara.malik@legalease.com", 100002, "Family Law", 5),
            ("omar.hassan@legalease.com", 100003, "Corporate Law", 12),
        ]:
            uid = user_ids[email]
            db.execute(text("DELETE FROM lawyer WHERE userid = :u"), {"u": uid})
            db.execute(
                text(
                    "INSERT INTO lawyer (barlicenseno, userid, specialization, experienceyears) "
                    "VALUES (:bar, :u, :spec, :exp)"
                ),
                {"bar": bar, "u": uid, "spec": spec, "exp": exp},
            )
            lawyers.append(
                db.execute(
                    text("SELECT lawyerid FROM lawyer WHERE userid = :u"), {"u": uid}
                ).fetchone()[0]
            )

        judge_uid = user_ids["test@judge.com"]
        db.execute(text("DELETE FROM judge WHERE userid = :u"), {"u": judge_uid})
        db.execute(
            text(
                "INSERT INTO judge (userid, position, specialization, expyears) "
                "VALUES (:u, :pos, :spec, :exp)"
            ),
            {"u": judge_uid, "pos": "District & Sessions Judge", "spec": "Criminal Law", "exp": 15},
        )
        judge_id = db.execute(
            text("SELECT judgeid FROM judge WHERE userid = :u"), {"u": judge_uid}
        ).fetchone()[0]

        reg_uid = user_ids["registrar@legalease.com"]

        # Court
        court = db.execute(text("SELECT courtid FROM court LIMIT 1")).fetchone()
        if not court:
            court_id = db.execute(
                text(
                    "INSERT INTO court (courtname, type, location) "
                    "VALUES ('Lahore District Court', 'District', 'Fane Road, Lahore') "
                    "RETURNING courtid"
                )
            ).fetchone()[0]
        else:
            court_id = court[0]

        db.execute(text("DELETE FROM courtregistrar WHERE userid = :u"), {"u": reg_uid})
        db.execute(
            text("INSERT INTO courtregistrar (userid, courtid, position) VALUES (:u, :c, :p)"),
            {"u": reg_uid, "c": court_id, "p": "Senior Registrar"},
        )

        db.execute(
            text(
                "INSERT INTO judgeworksin (judgeid, courtid) VALUES (:j, :c) "
                "ON CONFLICT DO NOTHING"
            ),
            {"j": judge_id, "c": court_id},
        )

        # Cases
        cases_data = [
            ("State v. Ali Raza", "Theft and possession case", "Criminal", "Open", "2024-06-01"),
            ("Khan Family Custody Dispute", "Child custody matter", "Family", "Pending", "2024-08-15"),
            ("TechCorp Contract Breach", "Commercial dispute", "Corporate", "Open", "2025-01-10"),
        ]
        case_ids = []
        for title, desc, ctype, status, filing in cases_data:
            existing = db.execute(
                text("SELECT caseid FROM cases WHERE title = :t"), {"t": title}
            ).fetchone()
            if existing:
                cid = existing[0]
            else:
                cid = db.execute(
                    text(
                        "INSERT INTO cases (title, description, casetype, status, filingdate) "
                        "VALUES (:t, :d, :ct, :s, :f) RETURNING caseid"
                    ),
                    {"t": title, "d": desc, "ct": ctype, "s": status, "f": filing},
                ).fetchone()[0]
            case_ids.append(cid)
            db.execute(
                text(
                    "INSERT INTO courtaccess (courtid, caseid) VALUES (:c, :case) "
                    "ON CONFLICT DO NOTHING"
                ),
                {"c": court_id, "case": cid},
            )
            db.execute(
                text(
                    "INSERT INTO caselawyeraccess (lawyerid, caseid) VALUES (:l, :case) "
                    "ON CONFLICT DO NOTHING"
                ),
                {"l": lawyers[case_ids.index(cid) % len(lawyers)], "case": cid},
            )
            db.execute(
                text(
                    "INSERT INTO judgeaccess (judgeid, caseid) VALUES (:j, :case) "
                    "ON CONFLICT DO NOTHING"
                ),
                {"j": judge_id, "case": cid},
            )
            db.execute(
                text(
                    "INSERT INTO caseparticipantaccess (participantid, caseid) "
                    "VALUES (:p, :case) ON CONFLICT DO NOTHING"
                ),
                {"p": participant_id, "case": cid},
            )

        # Documents for client cases
        for i, cid in enumerate(case_ids):
            doc_id = db.execute(
                text(
                    "INSERT INTO documents (documenttitle, documenttype, uploaddate, filepath) "
                    "VALUES (:title, :type, :ud, :path) RETURNING documentid"
                ),
                {
                    "title": f"Case Filing Pack {i + 1}.pdf",
                    "type": "Legal Documents",
                    "ud": date.today(),
                    "path": f"/uploads/case_{cid}_filing.pdf",
                },
            ).fetchone()[0]
            db.execute(
                text(
                    "INSERT INTO documentcase (caseid, documentid, submissiondate) "
                    "VALUES (:c, :d, :sd) ON CONFLICT DO NOTHING"
                ),
                {"c": cid, "d": doc_id, "sd": date.today()},
            )

        # Hearings
        next_hid = db.execute(
            text("SELECT COALESCE(MAX(hearingid), 0) + 1 FROM hearings")
        ).fetchone()[0]
        for cid in case_ids:
            title = db.execute(
                text("SELECT title FROM cases WHERE caseid = :c"), {"c": cid}
            ).fetchone()[0]
            db.execute(
                text(
                    "INSERT INTO hearings (caseid, hearingid, judgeid, hearingdate, "
                    "hearingtime, remarks, venue) "
                    "VALUES (:case, :hid, :j, :hd, :ht, :rm, :v)"
                ),
                {
                    "case": cid,
                    "hid": next_hid,
                    "j": judge_id,
                    "hd": date(2026, 6, 16),
                    "ht": time(10, 0),
                    "rm": f"Initial hearing for {title}",
                    "v": "Courtroom 3",
                },
            )
            next_hid += 1

        # Case history
        for cid in case_ids:
            db.execute(
                text(
                    "INSERT INTO casehistory (caseid, actiondate, actiontaken, remarks) "
                    "VALUES (:c, :d, :a, :r)"
                ),
                {
                    "c": cid,
                    "d": date.today(),
                    "a": "Case registered in system",
                    "r": "Seed data entry",
                },
            )

        # Admin logs
        admin_row = db.execute(
            text("SELECT adminid FROM admin WHERE userid = :u"), {"u": admin_uid}
        ).fetchone()
        if admin_row:
            db.execute(text("DELETE FROM logtable"))
            for action, desc, entity in [
                ("CREATE", "New case registered: State v. Ali Raza", "case"),
                ("UPDATE", "Hearing scheduled for custody dispute", "case"),
                ("LOGIN", "Admin reviewed system activity", "admin"),
            ]:
                db.execute(
                    text(
                        "INSERT INTO logtable (adminid, actiontype, description, status, entitytype) "
                        "VALUES (:a, :t, :d, 'Success', :e)"
                    ),
                    {"a": admin_row[0], "t": action, "d": desc, "e": entity},
                )

        db.commit()
        print("=" * 60)
        print("Database seeded successfully!")
        print(f"Password for ALL accounts: {DEFAULT_PASSWORD}")
        print("=" * 60)
        print("\nLogin accounts:")
        for role, fn, ln, email, *_ in users_spec:
            print(f"  [{role:16}] {email}")
        print()

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
