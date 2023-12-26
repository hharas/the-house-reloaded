"""
The House reloaded
Routes
"""

from flask import Blueprint

api = Blueprint("api", __name__, url_prefix="/api")


@api.get('/')
def index():
    """Homepage"""

    return "It's working!"
