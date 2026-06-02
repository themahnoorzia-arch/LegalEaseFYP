from flask import Blueprint

legal_actors_bp = Blueprint(
    "legal_actors",
    __name__,
    url_prefix="/api"
)

from . import routes