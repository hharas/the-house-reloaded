"""
The House reloaded
Before-request callbacks
"""

from flask import session
from flask_login import current_user, logout_user


def set_default_theme():
    """Load the light theme by default if there's no set theme"""
    if "theme" not in session:
        session["theme"] = "light"


def logout_if_deleted():
    """Logout a user if his account has been deleted"""
    if current_user.is_authenticated:
        if current_user.deleted:
            logout_user()
