from flask import Blueprint

court_bp = Blueprint(
    "court",
    __name__
)

from . import routes