"""
extensions.py
-------------
Flask extension instances, initialised without an app object (application
factory pattern).  Import from here in blueprints and services — never from
app.py — to avoid circular imports.

Usage in your app factory (app.py):
    from extensions import register_extensions
    register_extensions(app)

Usage anywhere else (blueprints, services, …):
    from extensions import login_manager, cors
"""

from __future__ import annotations

import logging

from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from flask_mail import Mail
from flask_session import Session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Extension singletons — created here, bound to the app inside
# register_extensions() below.
# ---------------------------------------------------------------------------
login_manager: LoginManager = LoginManager()
sess: Session = Session()
cors: CORS = CORS()
mail: Mail = Mail()


# ---------------------------------------------------------------------------
# User loader — kept here so login_manager is fully self-contained.
# Imports are deferred (inside the function) to prevent circular imports
# at module load time.
# ---------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id: str):
    """
    Reload a User object from the session's stored user_id.
    Called automatically by Flask-Login on every authenticated request.
    """
    from db.db import SessionLocal          # deferred — avoids circular import
    from models import Users                # deferred — avoids circular import

    db = SessionLocal()
    try:
        return db.query(Users).get(int(user_id))
    except Exception as exc:
        logger.error("load_user failed for user_id=%s: %s", user_id, exc)
        return None
    finally:
        db.close()


@login_manager.unauthorized_handler
def unauthorized():
    """
    Return a JSON 401 instead of Flask-Login's default HTML redirect.
    This keeps the API consistent for the React frontend.
    """
    return jsonify({"error": "Authentication required. Please log in."}), 401


# ---------------------------------------------------------------------------
# register_extensions — call once from create_app() / your app factory.
#
# Preserves the exact CORS config from the original app.py:
#   CORS(app, supports_credentials=True, origins=["http://localhost:3000"])
#
# To support additional origins in production, set CORS_ORIGINS in your
# environment / Config and pass it here.
# ---------------------------------------------------------------------------
def register_extensions(app: Flask) -> None:
    """
    Bind all Flask extensions to *app*.

    Call this exactly once, inside create_app(), after
    app.config.from_object(Config).
    """

    # -- Flask-Session -------------------------------------------------------
    # Reads SESSION_TYPE, SESSION_SQLALCHEMY, etc. from app.config.
    sess.init_app(app)

    # -- Flask-CORS ----------------------------------------------------------
    # Pull allowed origins from config so it's overridable without code change.
    # Falls back to the original hard-coded localhost:3000 if not set.
    allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
    ]

    cors.init_app(
        app,
        supports_credentials=True,
        origins=allowed_origins,
    )

    # -- Flask-Mail ----------------------------------------------------------
    mail.init_app(app)

    # -- Flask-Login ---------------------------------------------------------
    login_manager.init_app(app)

    # login_view is intentionally left unset — the @unauthorized_handler above
    # returns JSON 401 instead of redirecting, which is correct for a REST API.

    logger.info(
        "Extensions registered — CORS origins: %s",
        allowed_origins,
    )