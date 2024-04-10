"""
The House reloaded
Routes
"""

from flask import Blueprint, current_app, request

from .extensions import db
from .models import Category, Post, Thread, User
from .schemas import CategorySchema, PostSchema, ThreadSchema, UserSchema
from .utils import form_response

api = Blueprint("api", __name__, url_prefix="/api")


def authorize(payload):
    """Authorize an API User"""

    user = User.query.filter_by(
        token=payload.headers.get("Authorization")
    ).first()

    if user is not None:
        return user

    return None


@api.get('/')
def index():
    """API status message"""

    return "It's working!"


@api.get("/users/<username>/", strict_slashes=False)
def get_user(username: str):
    """Get a specific user by its id"""

    user_schema = UserSchema()

    user = User.query.filter_by(username=username).first()

    if not user or user.deleted:
        return form_response(error="User not found"), 404

    result = user_schema.dump(user)

    return form_response(result)


@api.get("/categories/", strict_slashes=False)
def get_categories():
    """Get all categories"""

    categories_schema = CategorySchema(many=True)

    categories = Category.query.filter_by(deleted=False).all()
    result = categories_schema.dump(categories)

    return form_response(result)


@api.get("/categories/<int:cat_id>/", strict_slashes=False)
def get_category(cat_id: int):
    """Get a specific category by its id"""

    category_schema = CategorySchema()

    category = Category.query.get(cat_id)

    if not category:
        return form_response(error="Category not found"), 404

    result = category_schema.dump(category)

    return form_response(result)


@api.get("/threads/", strict_slashes=False)
def get_threads():
    """Get all threads"""

    threads_schema = ThreadSchema(many=True)

    threads = Thread.query.filter_by(deleted=False).all()
    result = threads_schema.dump(threads)

    result.reverse()

    return form_response(result)


@api.get("/threads/<int:thread_id>/", strict_slashes=False)
def get_thread(thread_id: int):
    """Get a specific thread by its id"""

    thread_schema = ThreadSchema()

    thread = Thread.query.get(thread_id)

    if not thread:
        return form_response(error="Thread not found"), 404

    thread.views += 1
    db.session.commit()

    result = thread_schema.dump(thread)

    return form_response(result)


@api.get("/posts/", strict_slashes=False)
def get_posts():
    """Get all posts"""

    posts_schema = PostSchema(many=True)

    posts = Post.query.filter_by(deleted=False).all()
    result = posts_schema.dump(posts)

    result.reverse()

    return form_response(result)


@api.get("/posts/<int:post_id>/", strict_slashes=False)
def get_post(post_id: int):
    """Get a specific post by its id"""

    post_schema = PostSchema()

    post = Post.query.get(post_id)

    if not post:
        return form_response(error="Post not found"), 404

    result = post_schema.dump(post)

    return form_response(result)


@api.post("/promote/", strict_slashes=False)
def promote():
    """Promote a user to admin"""

    current_user = authorize(request)

    if current_user is not None:
        if current_app.config["ENABLE_ADMIN_KEY"]:
            if current_app.config["ADMIN_KEY"] is not None:
                if request.get_json().get("key") == current_app.config["ADMIN_KEY"]:
                    user = User.query.filter_by(id=current_user.id).first()
                    user.role = "admin"

                    db.session.add(user)
                    db.session.commit()

                    return form_response("Promoted Successfully!")

                    # TODO: What would it say if one's already promoted?

    return form_response(error="Not found"), 404


@api.get("/whoami/", strict_slashes=False)
def whoami():
    """Confirm a user's login"""

    user = authorize(request)

    if user is not None:
        return form_response(user.username)

    return form_response(None)
