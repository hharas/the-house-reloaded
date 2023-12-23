"""
The House reloaded
Utility functions
"""

import os
import sys
from uuid import uuid4

import bleach
from flask import current_app


def eprint(*args, **kwargs):
    """Print message to stderr"""
    print(*args, file=sys.stderr, **kwargs)


def generate_uploads_filename(file_data) -> str:
    """Generate filename based on attachment extension"""
    return str(uuid4())[:8] + '.' + \
        file_data.filename.rsplit(".")[-1]


def save_to_uploads(file_data, attachment_filename: str):
    """Save attachment into uploads directory"""
    file_data.save(os.path.join(
        current_app.config["UPLOADS_DIRECTORY"], attachment_filename))


def render_content(value: str) -> str:
    """Turn thread/post contents into renderable HTML"""
    cleaned = bleach.clean(value)
    linkified = bleach.linkify(cleaned, parse_email=True)
    nl2brd = linkified.replace('\n', "<br />")

    return nl2brd


def delete_upload(filename: str):
    """Delete an uploaded file"""
    try:
        os.remove(os.path.join(
            current_app.config["UPLOADS_DIRECTORY"], filename))
    except FileNotFoundError as error:
        eprint(error)
