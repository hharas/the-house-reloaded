"""
The House reloaded
App configuration
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:  # pylint: disable=too-few-public-methods
    """App config class"""
    SITE_NAME = os.getenv("THR_SITE_NAME") or "The House"
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "THR_DATABASE_URI") or "sqlite:///thehouse.db"
    SECRET_KEY = os.getenv("THR_SECRET_KEY")
    UPLOADS_DIRECTORY = os.getenv("THR_UPLOADS_DIRECTORY") or "uploads"
    ENABLE_ADMIN_KEY = os.getenv("THR_ENABLE_ADMIN_KEY") == "yes"
    ADMIN_KEY = None if not ENABLE_ADMIN_KEY else os.getenv("THR_ADMIN_KEY")
    PREVIEWABLE_EXTENSIONS = ["png", "jpeg", "jpg", "webp", "gif",
                              "mp4", "webm", "mp3", "ogg", "wav",
                              "flac", "alac", "m4a", "aac", "svg"]
