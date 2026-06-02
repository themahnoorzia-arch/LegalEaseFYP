"""Smoke-test frontend API routes against the running Flask app."""
import json
import urllib.error
import urllib.request
import http.cookiejar

BASE = "http://127.0.0.1:5000"

ROUTES = [
    ("GET", "/api/dashboard", None),
    ("GET", "/api/cases", None),
    ("GET", "/api/payments", None),
    ("GET", "/api/lawyerprofile", None),
    ("GET", "/api/hearings", None),
    ("GET", "/api/appeals", None),
    ("GET", "/api/lawyerappeals", None),
    ("GET", "/api/bails", None),
    ("GET", "/api/surety/from-lawyer", None),
    ("GET", "/api/evidence", None),
    ("GET", "/api/lawyer/evidence", None),
    ("GET", "/api/witnesses", None),
    ("GET", "/api/documents", None),
    ("GET", "/api/judges", None),
    ("GET", "/api/prosecutors", None),
    ("GET", "/api/remands", None),
    ("GET", "/api/logs", None),
    ("GET", "/api/adminprofile", None),
    ("GET", "/api/clientprofile", None),
    ("GET", "/api/judgeprofile", None),
    ("GET", "/api/registrarprofile", None),
    ("GET", "/api/court", None),
]


def main():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    login_body = json.dumps(
        {"email": "proftest2@test.com", "password": "password123"}
    ).encode()
    login_req = urllib.request.Request(
        BASE + "/api/login",
        data=login_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener.open(login_req)

    print("Lawyer session (proftest2@test.com):\n")
    for method, path, _ in ROUTES:
        req = urllib.request.Request(BASE + path, method=method)
        try:
            resp = opener.open(req)
            status = resp.status
        except urllib.error.HTTPError as e:
            status = e.code
        label = "OK" if status != 404 else "MISSING"
        print(f"  [{label}] {method} {path} -> {status}")


if __name__ == "__main__":
    main()
