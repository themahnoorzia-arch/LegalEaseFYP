from flask import Blueprint

financials_bp = Blueprint(
    "financials",
    __name__
)

from . import routes