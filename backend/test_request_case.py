"""Verify lawyer case request creates a persisted case with lawyer link."""
import json

from app import app
from db.db import get_pg_connection


def run():
    client = app.test_client()

    login = client.post(
        "/api/login",
        json={"email": "sara.malik@legalease.com", "password": "LegalEase2025!"},
    )
    assert login.status_code == 200, login.get_json()

    payload = {
        "title": "divorce case test",
        "description": "Automated test filing",
        "casetype": "Family",
        "clientName": "Zaina Zia",
        "courtname": "Lahore District Court",
        "side": "Petitioner",
    }
    res = client.post("/api/cases", json=payload)
    body = res.get_json()
    print("POST /api/cases:", res.status_code, body)
    assert res.status_code == 201, body
    case_id = body["case_id"]

    cases_res = client.get("/api/cases")
    cases_body = cases_res.get_json()
    assert cases_res.status_code == 200
    titles = [c["title"] for c in cases_body.get("cases", [])]
    assert "divorce case test" in titles, titles

    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT status FROM cases WHERE caseid = %s",
        (case_id,),
    )
    case_status = cur.fetchone()[0]
    assert case_status == "Pending", case_status

    cur.execute(
        """
        SELECT cla.status, cla.side
        FROM caselawyeraccess cla
        JOIN lawyer l ON l.lawyerid = cla.lawyerid
        JOIN users u ON u.userid = l.userid
        WHERE cla.caseid = %s AND u.email = %s
        """,
        (case_id, "sara.malik@legalease.com"),
    )
    link = cur.fetchone()
    assert link is not None, "Lawyer not linked to new case"
    assert link[0] == "approved", link
    assert link[1] == "petitioner", link

    cur.execute(
        """
        SELECT 1 FROM courtaccess ca
        JOIN court c ON c.courtid = ca.courtid
        WHERE ca.caseid = %s AND c.courtname = %s
        """,
        (case_id, "Lahore District Court"),
    )
    assert cur.fetchone() is not None, "Case not linked to court"

    conn.close()

    # Registrar should see the pending case in their court
    client.post("/api/logout")
    reg_login = client.post(
        "/api/login",
        json={"email": "registrar@legalease.com", "password": "LegalEase2025!"},
    )
    assert reg_login.status_code == 200

    reg_cases = client.get("/api/cases")
    reg_body = reg_cases.get_json()
    reg_titles = [c["title"] for c in reg_body.get("cases", [])]
    assert "divorce case test" in reg_titles, reg_titles

    print("All checks passed.")


if __name__ == "__main__":
    run()
