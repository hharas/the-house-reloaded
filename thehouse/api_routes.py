"""
The House reloaded
Routes
"""

from flask import Blueprint

from .extensions import db
from .models import Category, Post, Thread, User
from .schemas import CategorySchema, PostSchema, ThreadSchema, UserSchema
from .utils import form_response

api = Blueprint("api", __name__, url_prefix="/api")


@api.get("/")
def get_categories():
    """Get all categories"""

    categories_schema = CategorySchema(many=True)

    categories = Category.query.filter_by(deleted=False).all()
    result = categories_schema.dump(categories)

    return form_response(result)


@api.get("/<cat_title>/", strict_slashes=False)
def get_category(cat_title: str):
    """Get a specific category by its id"""

    category_schema = CategorySchema()

    category = Category.query.filter_by(title=cat_title).first()

    if not category:
        return form_response(error="Category not found"), 404

    result = category_schema.dump(category)

    return form_response(result)


@api.get("/<cat_title>/<int:thread_id>/", strict_slashes=False)
def get_thread(cat_title: str, thread_id: int):
    """Get a specific thread by its id"""

    thread_schema = ThreadSchema()

    category = Category.query.filter_by(title=cat_title).first()
    thread = Thread.query.filter_by(id=thread_id, cat_id=category.id).first()

    if not thread:
        return form_response(error="Thread not found"), 404

    thread.views += 1
    db.session.commit()

    result = thread_schema.dump(thread)

    return form_response(result)


@api.get("/<cat_title>/<int:thread_id>/<int:post_id>/", strict_slashes=False)
def get_post(cat_title: str, thread_id: int, post_id: int):
    """Get a specific post by its id"""

    post_schema = PostSchema()

    category = Category.query.filter_by(title=cat_title).first()
    thread = Thread.query.filter_by(id=thread_id, cat_id=category.id).first()
    post = Post.query.filter_by(
        id=post_id, cat_id=category.id, thread_id=thread.id).first()

    if not post:
        return form_response(error="Post not found"), 404

    result = post_schema.dump(post)

    return form_response(result)


@api.get("/~<username>/", strict_slashes=False)
def get_user(username: str):
    """Get a specific user by its id"""

    user_schema = UserSchema()

    user = User.query.filter_by(username=username).first()

    if not user or user.deleted:
        return form_response(error="User not found"), 404

    result = user_schema.dump(user)

    return form_response(result)
