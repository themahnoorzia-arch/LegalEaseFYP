"""
utils/helpers.py
----------------
Shared utilities used across all blueprints:

  - Role constants          (single source of truth for role strings)
  - require_roles()         (route decorator for role-based access control)
  - serialize_date()        (safe date/datetime → ISO string)
  - serialize_decimal()     (Decimal → float for JSON)
  - success_response()      (standard JSON success envelope)
  - error_response()        (standard JSON error envelope)

Import examples:
    from utils.helpers import require_roles, Roles
    from utils.helpers import serialize_date, serialize_decimal
    from utils.helpers import success_response, error_response
"""

from __future__ import annotations

import datetime
import logging
from decimal import Decimal
from functools import wraps
from typing import Any

from flask import jsonify
from flask_login import current_user

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Role constants
# Single source of truth — matches the CHECK constraint in models.py exactly:
#   ('Admin', 'Lawyer', 'Judge', 'CourtRegistrar', 'CaseParticipant')
# ---------------------------------------------------------------------------
class Roles:
    ADMIN            = "Admin"
    LAWYER           = "Lawyer"
    JUDGE            = "Judge"
    COURT_REGISTRAR  = "CourtRegistrar"
    CASE_PARTICIPANT = "CaseParticipant"

    ALL = {ADMIN, LAWYER, JUDGE, COURT_REGISTRAR, CASE_PARTICIPANT}

    # Mapping used during signup/login to normalise free-text → DB value.
    # Mirrors the role_mapping dict that appears in multiple routes in app.py.
    NORMALISE_MAP: dict[str, str] = {
        "admin":            ADMIN,
        "lawyer":           LAWYER,
        "judge":            JUDGE,
        "courtregistrar":   COURT_REGISTRAR,
        "court registrar":  COURT_REGISTRAR,
        "registrar":        COURT_REGISTRAR,
        "caseparticipant":  CASE_PARTICIPANT,
        "case participant": CASE_PARTICIPANT,
        "client":           CASE_PARTICIPANT,
    }

    @classmethod
    def normalise(cls, raw: str) -> str | None:
        """
        Convert a free-text role string to its canonical DB value.
        Returns None if the value is not recognised.

        >>> Roles.normalise("client")
        'CaseParticipant'
        >>> Roles.normalise("JUDGE")
        'Judge'
        """
        return cls.NORMALISE_MAP.get(raw.strip().lower())

    @classmethod
    def is_valid(cls, role: str) -> bool:
        """Return True if *role* is a recognised DB role value."""
        return role in cls.ALL


# ---------------------------------------------------------------------------
# require_roles — route decorator for role-based access control
#
# Usage (single role):
#   @app.route("/api/judges")
#   @login_required
#   @require_roles(Roles.ADMIN, Roles.COURT_REGISTRAR)
#   def get_judges():
#       ...
#
# The decorator must be applied AFTER @login_required so current_user
# is already populated when the check runs.
# ---------------------------------------------------------------------------
def require_roles(*roles: str):
    """
    Decorator that restricts a route to users whose role is in *roles*.

    Returns HTTP 403 JSON if the authenticated user's role is not allowed.
    Must be used after @login_required.
    """
    allowed = set(roles)

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                # Shouldn't happen when used after @login_required,
                # but guard defensively.
                return error_response("Authentication required.", 401)

            if current_user.role not in allowed:
                logger.warning(
                    "Access denied: user %s (role=%s) tried to access %s",
                    current_user.userid,
                    current_user.role,
                    fn.__name__,
                )
                return error_response(
                    f"Access denied. Required role(s): {', '.join(sorted(allowed))}.",
                    403,
                )

            return fn(*args, **kwargs)

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Date / Decimal serializers
# Replaces the repeated  `x.isoformat() if x else None`  pattern in app.py.
# ---------------------------------------------------------------------------
def serialize_date(
    value: datetime.date | datetime.datetime | None,
) -> str | None:
    """
    Return an ISO-8601 string for a date or datetime, or None if falsy.

    >>> serialize_date(datetime.date(2024, 1, 15))
    '2024-01-15'
    >>> serialize_date(None)
    None
    """
    if value is None:
        return None
    return value.isoformat()


def serialize_time(value: datetime.time | None) -> str | None:
    """
    Return an ISO-8601 time string, or None if falsy.

    >>> serialize_time(datetime.time(9, 30))
    '09:30:00'
    """
    if value is None:
        return None
    return value.isoformat()


def serialize_decimal(value: Decimal | float | None) -> float | None:
    """
    Convert a Decimal (from Numeric DB columns) to a plain float for JSON.
    Returns None if the value is falsy.

    >>> serialize_decimal(Decimal("1234.56"))
    1234.56
    """
    if value is None:
        return None
    return float(value)


# ---------------------------------------------------------------------------
# Standard JSON response envelopes
# Keeps HTTP status codes and response shapes consistent across all blueprints.
# ---------------------------------------------------------------------------
def success_response(
    data: Any = None,
    message: str = "Success",
    status: int = 200,
):
    """
    Return a JSON success response.

    Shape:
        { "success": true, "message": "...", "data": <payload> }

    *data* is omitted from the envelope when None to keep responses lean.
    """
    body: dict[str, Any] = {"success": True, "message": message}
    if data is not None:
        body["data"] = data
    return jsonify(body), status


def error_response(
    message: str = "An unexpected error occurred.",
    status: int = 400,
    details: Any = None,
):
    """
    Return a JSON error response.

    Shape:
        { "success": false, "error": "...", "details": <optional> }

    *details* is omitted when None.
    """
    body: dict[str, Any] = {"success": False, "error": message}
    if details is not None:
        body["details"] = details
    return jsonify(body), status


# ---------------------------------------------------------------------------
# Role → display label mapping
# Mirrors the "Client" alias used in the /api/dashboard route in app.py.
# ---------------------------------------------------------------------------
ROLE_DISPLAY_MAP: dict[str, str] = {
    Roles.CASE_PARTICIPANT: "Client",
    Roles.COURT_REGISTRAR:  "CourtRegistrar",
    Roles.LAWYER:           "Lawyer",
    Roles.JUDGE:            "Judge",
    Roles.ADMIN:            "Admin",
}


def display_role(role: str) -> str:
    """
    Return the display-friendly label for a DB role string.
    Falls back to the raw value if not in the map.

    >>> display_role("CaseParticipant")
    'Client'
    """
    return ROLE_DISPLAY_MAP.get(role, role)