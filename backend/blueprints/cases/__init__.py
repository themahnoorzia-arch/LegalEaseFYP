from flask import Blueprint

cases_bp = Blueprint(
    "cases",
    __name__,
    url_prefix="/api"
)

from . import case_routes
from . import hearing_routes
from . import appeal_routes
from . import support_routes
from . import extra_routes