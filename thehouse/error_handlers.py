"""
The House reloaded
Error handler functions
"""

from flask import render_template

from .utils import form_response


def handle_page_not_found(_):
    """Handle viewing a non-existent page"""

    return render_template("404.html"), 404


def main_handle_method_not_allowed(_):
    """Handle using unallowed methods"""

    return render_template("405.html"), 405


def main_handle_server_error(_):
    """Handle server errors"""

    return render_template("500.html"), 500


def api_handle_method_not_allowed(_):
    """Handle using unallowed methods (API)"""

    return form_response(error="Method not allowed"), 405


def api_handle_server_error(_):
    """Handle server errors (API)"""

    return form_response(error="Server error"), 500
