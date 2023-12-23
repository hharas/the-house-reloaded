"""
The House reloaded
Error handler functions
"""

from flask import render_template


def handle_page_not_found(_):
    """Handle viewing a non-existent page"""

    return render_template("404.html"), 404


def handle_method_not_allowed(_):
    """Handle using unallowed methods"""

    return render_template("405.html"), 405


def handle_server_error(_):
    """Handle server errors"""

    return render_template("500.html"), 500
