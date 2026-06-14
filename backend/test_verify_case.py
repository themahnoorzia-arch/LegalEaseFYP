"""Verify registrar case verification endpoint."""
from app import app
from db.db import get_pg_connection


def run():
    client = app.test_client()

    reg = client.post(
        "/api/login",
        json={"email": "registrar@legalease.com", "password": "LegalEase2025!"},
    )
    assert reg.status_code == 200, reg.get_json()

    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT caseid FROM cases
        WHERE title = 'divorce case test' AND status = 'Pending'
        ORDER BY caseid DESC LIMIT 1
        """
    )
    row = cur.fetchone()
    if not row:
        print("No pending divorce case test — skipping")
        conn.close()
        return

    caseid = row[0]
    conn.close()

    payload = {
        "caseid": caseid,
        "casename": "divorce case test",
        "type": "Family",
        "filingdate": "2026-06-07",
        "clientname": "Zaina Zia",
        "lawyername": "Sara Malik",
        "judgename": "Test Judge",
    }
    res = client.post("/api/verifycases", json=payload)
    body = res.get_json()
    print("POST /api/verifycases:", res.status_code, body)
    assert res.status_code == 200, body

    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT status, casenumber FROM cases WHERE caseid = %s",
        (caseid,),
    )
    status, casenumber = cur.fetchone()
    assert status == "Open", status
    assert casenumber, f"Expected auto-assigned case number, got: {casenumber}"
    assert body.get("casenumber") == casenumber
    cur.execute(
        "SELECT 1 FROM judgeaccess WHERE caseid = %s",
        (caseid,),
    )
    assert cur.fetchone() is not None
    conn.close()
    print("Verify case test passed.")


if __name__ == "__main__":
    run()
