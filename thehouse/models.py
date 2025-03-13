"""
The House reloaded
Database models
"""

from uuid import uuid4

from flask_login import UserMixin

from .extensions import db
from .utils import delete_upload


class User(db.Model, UserMixin):  # pylint: disable=too-few-public-methods
    """A Housean user"""

    id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid4()), unique=True
    )
    token = db.Column(db.String(36), default=lambda: str(uuid4()), unique=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    joined_date = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    role = db.Column(
        db.Enum("admin", "moderator", "user", name="user_roles"), default="user"
    )
    picture_filename = db.Column(db.Text)
    bio = db.Column(db.String(60))
    deleted = db.Column(db.Boolean, nullable=False, default=False)

    def delete(self):
        """Demote the user and flag him as deleted"""

        self.deleted = True
        self.role = "user"

        if self.picture_filename:
            delete_upload(self.picture_filename)
            self.picture_filename = None


class Category(db.Model):  # pylint: disable=too-few-public-methods
    """A Housean category or board"""

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False, unique=True)
    description = db.Column(db.String(150), nullable=False)
    deleted = db.Column(db.Boolean, nullable=False, default=False)

    def delete(self):
        """Remove category description and flag it as deleted"""

        self.deleted = True
        self.description = ""


class Thread(db.Model):  # pylint: disable=too-few-public-methods
    """A Casual thread"""

    id = db.Column(db.Integer, primary_key=True)
    cat_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    creator = db.Column(db.String(36), nullable=False)
    content = db.Column(db.Text)
    attachment_filename = db.Column(db.Text)
    creation_date = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    views = db.Column(db.Integer, nullable=False, default=0)
    deleted = db.Column(db.Boolean, nullable=False, default=False)

    def delete(self):
        """Remove thread contents and flag it as deleted"""

        self.deleted = True
        self.title = ""
        self.content = ""

        if self.attachment_filename:
            delete_upload(self.attachment_filename)
            self.attachment_filename = None


class Post(db.Model):  # pylint: disable=too-few-public-methods
    """A post on the House"""

    id = db.Column(db.Integer, primary_key=True)
    cat_id = db.Column(db.Integer, nullable=False)
    thread_id = db.Column(db.Integer, nullable=False)
    author = db.Column(db.String(36), nullable=False)
    content = db.Column(db.Text, nullable=False)
    creation_date = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    replying_to = db.Column(db.Integer)
    attachment_filename = db.Column(db.Text)
    deleted = db.Column(db.Boolean, nullable=False, default=False)

    def delete(self):
        """Remove post contents and flag it as deleted"""
        self.deleted = True
        self.content = ""

        if self.attachment_filename:
            delete_upload(self.attachment_filename)
            self.attachment_filename = None
