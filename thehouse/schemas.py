"""
The House reloaded
Datbase model schemas
"""

from flask import url_for
from marshmallow import post_dump

from .extensions import ma
from .models import Category, Post, Thread, User


class UserSchema(ma.SQLAlchemyAutoSchema):
    """Schema for user model"""

    class Meta:  # pylint: disable=missing-class-docstring disable=too-few-public-methods
        model = User

    @post_dump
    def exclude_fields(self, data, **kwargs):  # pylint: disable=unused-argument
        """Exclude confidential user information"""
        fields_to_exclude = ["id", "token", "password"]

        for field in fields_to_exclude:
            data.pop(field, None)

        return data

    @post_dump
    def add_picture_url(self, data, **kwargs):  # pylint: disable=unused-argument
        """Add a picture_url field replacing picture_filename"""

        if data["picture_filename"]:
            data["picture_url"] = url_for(
                "main.uploads", filename=data["picture_filename"], _external=True
            )
        else:
            data["picture_url"] = None

        del data["picture_filename"]

        return data

    @post_dump
    def add_recent_activities(self, data, **kwargs):  # pylint: disable=unused-argument
        """Add recent_activities field"""

        activities = []

        for thread in Thread.query.filter_by(creator=data["id"], deleted=False).all():
            activities.append(
                {"type": "thread_creation", "data": ThreadSchema().dump(thread)}
            )

        for post in Post.query.filter_by(author=data["id"], deleted=False).all():
            activities.append({"type": "new_post", "data": PostSchema().dump(post)})

        activities = sorted(
            activities,
            key=lambda activity: activity["data"]["creation_date"],
            reverse=True,
        )

        data["recent_activities"] = []

        for activity in activities:
            data["recent_activities"].append(
                {"type": activity["type"], "id": activity["data"]["id"]}
                if activity["type"] == "thread_creation"
                else {"type": activity["type"], "id": activity["data"]["id"]}
            )

        return data


class CategorySchema(ma.SQLAlchemyAutoSchema):
    """Schema for category model"""

    class Meta:  # pylint: disable=missing-class-docstring disable=too-few-public-methods
        model = Category

    @post_dump
    def add_threads(self, data, **kwargs):  # pylint: disable=unused-argument
        """Add threads field"""

        data["threads"] = []

        for thread in Thread.query.filter_by(cat_id=data["id"], deleted=False).all():
            data["threads"].append(thread.id)

        return data

    @post_dump
    def add_last_activity(self, data, **kwargs):  # pylint: disable=unused-argument
        """Add last_activity field"""

        activities = []

        for thread in Thread.query.filter_by(cat_id=data["id"], deleted=False):
            if not User.query.filter_by(id=thread.creator).first().deleted:
                activities.append(
                    {"type": "thread_creation", "data": ThreadSchema().dump(thread)}
                )
        for post in Post.query.filter_by(cat_id=data["id"], deleted=False):
            if not User.query.filter_by(id=post.author).first().deleted:
                activities.append({"type": "new_post", "data": PostSchema().dump(post)})

        activities = sorted(
            activities,
            key=lambda activity: activity["data"]["creation_date"],
        )

        last_activity = activities[-1] if len(activities) != 0 else None

        data["last_activity"] = (
            (
                {
                    "type": last_activity["type"],
                    "id": last_activity["data"]["id"],
                }
                if last_activity["type"] == "thread_creation"
                else {
                    "type": last_activity["type"],
                    "id": last_activity["data"]["id"],
                }
            )
            if last_activity
            else None
        )

        return data


class ThreadSchema(ma.SQLAlchemyAutoSchema):
    """Schema for thread model"""

    class Meta:  # pylint: disable=missing-class-docstring disable=too-few-public-methods
        model = Thread

    @post_dump
    def replace_creator(self, data, **kwargs):  # pylint: disable=unused-argument
        """Replace creator field with a User"""

        creator = User.query.get(data["creator"])

        data["creator"] = creator.username if not creator.deleted else None

        return data

    @post_dump
    def replace_attachment_filename(self, data, **kwargs):  # pylint: disable=unused-argument
        """replace attachment_filename field with attachment_url"""
        data["attachment_url"] = (
            url_for(
                "main.uploads", filename=data["attachment_filename"], _external=True
            )
            if data["attachment_filename"]
            else None
        )

        del data["attachment_filename"]

        return data

    @post_dump
    def add_posts(self, data, **kwargs):  # pylint: disable=unused-argument
        """Add posts under this thread"""

        data["posts"] = []

        for post in Post.query.filter_by(thread_id=data["id"]).all():
            data["posts"].append(post.id)

        return data


class PostSchema(ma.SQLAlchemyAutoSchema):
    """Schema for post model"""

    class Meta:  # pylint: disable=missing-class-docstring disable=too-few-public-methods
        model = Post

    @post_dump
    def replace_author(self, data, **kwargs):  # pylint: disable=unused-argument
        """Replace author id with username"""

        author = User.query.get(data["author"])

        data["author"] = author.username if not author.deleted else None

        return data

    @post_dump
    def replace_attachment_filename(self, data, **kwargs):  # pylint: disable=unused-argument
        """replace attachment_filename field with attachment_url"""
        data["attachment_url"] = (
            url_for(
                "main.uploads", filename=data["attachment_filename"], _external=True
            )
            if data["attachment_filename"]
            else None
        )

        del data["attachment_filename"]

        return data
