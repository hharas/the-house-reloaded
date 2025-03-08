"""
The House reloaded
Utility functions
"""

import os
import sys
from uuid import uuid4

import bleach
from flask import current_app, url_for


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


def get_inbox(current_user, db_post):
    """yield posts in the user's inbox"""

    user_post_ids = []

    for user_post in db_post.query.filter_by(author=current_user.id, deleted=False).all():
        user_post_ids.append(user_post.id)

    for post in db_post.query.filter_by(deleted=False).all():
        if post.author != current_user.id:
            if post.replying_to:
                if post.replying_to in user_post_ids:
                    yield post


def form_response(result="", error: str = "") -> dict:
    """Function that forms an API response"""

    return {
        "result": result or None,
        "error": error or None
    }


def generate_file_embed(filename: str, maxheight: int = 300) -> str:
    """Generate an HTML embed for the uploaded file"""
    result = ""

    extension = filename.rsplit('.')[-1]

    image_extensions = ["jpg", "jpeg", "webp", "png", "gif", "jxl"]
    video_extensions = ["mp4", "webm", "mov", "avi"]
    audio_extensions = ["flac", "mp3", "ogg", "opus", "m4a"]

    if extension in image_extensions:
        result += f"""<img
        src="{url_for("main.uploads", filename=filename)}"
        style="max-height: {maxheight}px; margin-top: 5px"
        />"""
    elif extension in video_extensions:
        result += f"""<video height={maxheight} style='margin-top: 5px' controls>
        <source src="{url_for("main.uploads", filename=filename)}">
        Error: Your browser does not support the audio element.
        </video>"""
    elif extension in audio_extensions:
        result += f"""<audio controls>
        <source src="{url_for("main.uploads", filename=filename)}">
        Error: Your browser does not support the audio element.
        </audio>"""
    else:
        # Straight up return
        return f'<a href="{url_for("main.uploads", filename=filename)}">{filename}</a>'

    return result
