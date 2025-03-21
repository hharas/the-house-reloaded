"""
The House reloaded
API Routes
"""

from flask import Blueprint, current_app, request

from .extensions import db
from .models import Category, Post, Thread, User
from .schemas import CategorySchema, PostSchema, ThreadSchema, UserSchema
from .utils import (
    delete_upload,
    form_response,
    generate_uploads_filename,
    get_inbox,
    save_to_uploads,
)

api = Blueprint("api", __name__, url_prefix="/api")


def authorize(payload):
    """Authorize an API User"""

    user = User.query.filter_by(token=payload.headers.get("Authorization")).first()

    if user is not None:
        if not user.deleted:
            return user

    return None


@api.get("/")
def index():
    """API status message"""

    return form_response("It's working!")


@api.get("/whoami/", strict_slashes=False)
def whoami():
    """Confirm a user's login"""

    user = authorize(request)

    if user is not None:
        return form_response(user.username)

    return form_response(None)


@api.get("/inbox/", strict_slashes=False)
def inbox():
    """Retrieve the user's reply inbox"""

    current_user = authorize(request)

    if current_user is not None:
        post_schema = PostSchema()

        inbox_posts = []

        for post in get_inbox(current_user, Post):
            inbox_posts.append(post_schema.dump(post))

        inbox_posts.reverse()  # Show more recent posts first

        return form_response(inbox_posts)

    return form_response("Unauthorized"), 401


@api.post("/promote/", strict_slashes=False)
def promote():
    """Promote a user to admin"""

    current_user = authorize(request)

    if (
        (current_user is not None)
        and (current_user.role != "admin")
        and (current_app.config["ENABLE_ADMIN_KEY"])
        and (current_app.config["ADMIN_KEY"] is not None)
        and ("key" in request.form)
        and (request.form["key"] == current_app.config["ADMIN_KEY"])
    ):
        user = User.query.filter_by(id=current_user.id).first()
        user.role = "admin"

        db.session.add(user)
        db.session.commit()

        return form_response("Promoted Successfully!")

    return form_response(error="Not found"), 404


@api.get("/users/<username>/", strict_slashes=False)
def get_user(username: str):
    """Get a specific user by its id"""

    user_schema = UserSchema()

    user = User.query.filter_by(username=username).first()

    if not user or user.deleted:
        return form_response(error="User not found"), 404

    result = user_schema.dump(user)

    return form_response(result)


@api.put("/users/<username>/", strict_slashes=False)
def update_user(username: str):
    """Update user data"""

    current_user = authorize(request)
    user = User.query.filter_by(username=username).first()

    if user:
        if not user.deleted:
            altered = False

            if "role" in request.form:
                if current_user.role == "admin":
                    if request.form["role"] == ("user" or "moderator"):
                        user.role = request.form["role"]
                        altered = True
                    else:
                        return form_response(error="Bad request"), 400

                return form_response("Unauthorized"), 401

            if "bio" in request.form:
                if (current_user.role == "admin") or (current_user.id == user.id):
                    user.bio = request.form["bio"].strip()
                    altered = True
                else:
                    return form_response("Unauthorized"), 401

            if "picture" in request.files:
                if (current_user.role == "admin") or (current_user.id == user.id):
                    picture = request.files["picture"]

                    if current_user.picture_filename:
                        delete_upload(current_user.picture_filename)

                    profile_picture_filename = generate_uploads_filename(picture)

                    current_user.picture_filename = profile_picture_filename

                    if len(current_user.picture_filename) > 0:
                        save_to_uploads(picture, current_user.picture_filename)

                    altered = True
                else:
                    return form_response("Unauthorized"), 401

            if altered:
                db.session.add(current_user)
                db.session.commit()

                return form_response("Changes committed successfully!")

            return form_response("No changes where made.")

    return form_response(error="User not found"), 404


@api.delete("/users/<username>/", strict_slashes=False)
def delete_user(username: str):
    """Delete a user"""

    current_user = authorize(request)
    user = User.query.filter_by(username=username).first()
    threads = Thread.query.filter_by(creator=user.id).all()
    posts = Post.query.filter_by(author=user.id).all()

    if user:
        if not user.deleted:
            if current_user.role == "admin" or current_user.id == user.id:
                for post in posts:  # pylint: disable=duplicate-code
                    if not post.deleted:  # pylint: disable=duplicate-code
                        post.delete()  # pylint: disable=duplicate-code
                        db.session.add(post)  # pylint: disable=duplicate-code

                for thread in threads:  # pylint: disable=duplicate-code
                    if not thread.deleted:  # pylint: disable=duplicate-code
                        thread.delete()  # pylint: disable=duplicate-code
                        db.session.add(thread)  # pylint: disable=duplicate-code

                user.delete()  # pylint: disable=duplicate-code
                db.session.add(user)  # pylint: disable=duplicate-code

                db.session.commit()  # pylint: disable=duplicate-code

                return form_response("User deleted successfully!")

            return form_response(error="Unauthorized"), 401

    return form_response(error="User not found"), 404


@api.post("/categories/", strict_slashes=False)
def create_category():
    """Create a category"""

    current_user = authorize(request)

    if current_user is not None:
        if current_user.role == "admin":
            if ("title" and "description") in request.form:
                category_schema = CategorySchema()

                new_category = Category(
                    title=request.form["title"], description=request.form["description"]
                )

                db.session.add(new_category)
                db.session.commit()

                result = category_schema.dump(new_category)

                return form_response(result)
            return form_response(error="Bad request"), 400

    return form_response(error="Unauthorized"), 401


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


@api.put("/categories/<int:cat_id>/", strict_slashes=False)
def update_category(cat_id: int):
    """Update a category"""

    current_user = authorize(request)
    category = Category.query.filter_by(id=cat_id).first()

    if category:
        if not category.deleted:
            if current_user.role == "admin":
                updated = False

                if "title" in request.form:
                    category.title = request.form["title"]
                    updated = True

                if "description" in request.form:
                    category.description = request.form["description"]
                    updated = True

                if updated:
                    db.session.add(category)
                    db.session.commit()

                    category_schema = CategorySchema()

                    result = category_schema.dump(category)

                    return form_response(result)

                return form_response("No changes were made.")

            return form_response(error="Unauthorized"), 401

    return form_response(error="Post not found"), 404


@api.delete("/categories/<int:cat_id>/", strict_slashes=False)
def delete_category(cat_id: int):
    """Delete a category"""

    current_user = authorize(request)
    category = Category.query.filter_by(id=cat_id).first()
    threads = Thread.query.filter_by(cat_id=category.id).all()
    posts = Post.query.filter_by(cat_id=category.id).all()

    if category:
        if not category.deleted:
            if current_user.role == "admin":
                for post in posts:  # pylint: disable=duplicate-code
                    if not post.deleted:  # pylint: disable=duplicate-code
                        post.delete()  # pylint: disable=duplicate-code
                        db.session.add(post)  # pylint: disable=duplicate-code

                for thread in threads:  # pylint: disable=duplicate-code
                    if not thread.deleted:  # pylint: disable=duplicate-code
                        thread.delete()  # pylint: disable=duplicate-code
                        db.session.add(thread)  # pylint: disable=duplicate-code

                category.delete()  # pylint: disable=duplicate-code
                db.session.add(category)  # pylint: disable=duplicate-code

                db.session.commit()  # pylint: disable=duplicate-code

                return form_response("Category deleted successfully!")

            return form_response(error="Unauthorized"), 401

    return form_response(error="Category not found"), 404


@api.post("/threads/", strict_slashes=False)
def create_thread():
    """Create a thread"""

    current_user = authorize(request)

    if current_user is not None:
        if ("cat_id" and "title" and "content") in request.form:
            cat_id = request.form["cat_id"].strip()
            title = request.form["title"].strip()
            content = request.form["content"].strip()
            attachment_filename = None

            if "attachment" in request.files:
                attachment = request.files["attachment"]

                attachment_filename = generate_uploads_filename(attachment)

                save_to_uploads(attachment, attachment_filename)

            new_thread = Thread(
                cat_id=cat_id,
                title=title,
                content=content,
                creator=current_user.id,
                attachment_filename=attachment_filename,
            )

            category = Category.query.filter_by(id=cat_id).first()

            db.session.add(new_thread)
            category.last_active_user = current_user.id
            category.last_activity_date = db.func.current_timestamp()
            db.session.commit()

            thread_schema = ThreadSchema()
            result = thread_schema.dump(new_thread)

            return result

        return form_response(error="Bad request"), 400

    return form_response(error="Unauthorized"), 401


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


@api.put("/threads/<int:thread_id>/", strict_slashes=False)
def update_thread(thread_id: int):
    """Update a thread"""

    current_user = authorize(request)
    thread = Thread.query.filter_by(id=thread_id).first()
    creator = User.query.filter_by(id=thread.creator).first()

    if thread:
        if not thread.deleted:
            if current_user.id == creator.id:
                updated = False

                if "title" in request.form:
                    thread.title = request.form["title"]
                    updated = True

                if "content" in request.form:
                    thread.content = request.form["content"]
                    updated = True

                if "attachment" in request.files:
                    attachment = request.files["attachment"]

                    if thread.attachment_filename:
                        delete_upload(thread.attachment_filename)

                    new_attachment_filename = generate_uploads_filename(attachment)

                    thread.attachment_filename = new_attachment_filename

                    if len(thread.attachment_filename) > 0:
                        save_to_uploads(attachment, thread.attachment_filename)

                    updated = True

                if updated:
                    db.session.add(thread)
                    db.session.commit()

                    thread_schema = ThreadSchema()

                    result = thread_schema.dump(thread)

                    return form_response(result)

                return form_response("No changes were made.")

            return form_response(error="Unauthorized"), 401

    return form_response(error="Post not found"), 404


@api.delete("/threads/<int:thread_id>/", strict_slashes=False)
def delete_thread(thread_id: int):
    """Delete a thread"""

    current_user = authorize(request)
    thread = Thread.query.filter_by(id=thread_id).first()
    creator = User.query.filter_by(id=thread.creator).first()

    if thread:
        if not thread.deleted:
            if (
                current_user.role == "admin"
                or (current_user.role == "moderator" and creator.role == "user")
                or current_user.id == creator.id
            ):
                for post in Post.query.filter_by(thread_id=thread.id).all():  # pylint: disable=duplicate-code
                    post.delete()  # pylint: disable=duplicate-code
                    db.session.add(post)  # pylint: disable=duplicate-code

                thread.delete()  # pylint: disable=duplicate-code
                db.session.add(thread)  # pylint: disable=duplicate-code
                db.session.commit()  # pylint: disable=duplicate-code

                return form_response("Thread deleted successfully!")

            return form_response(error="Unauthorized"), 401

    return form_response(error="Thread not found"), 404


@api.post("/posts/", strict_slashes=False)
def create_post():
    """Create a post"""

    current_user = authorize(request)

    if current_user is not None:
        if ("cat_id" and "thread_id" and "content") in request.form:
            cat_id = request.form["cat_id"].strip()
            thread_id = request.form["thread_id"].strip()
            content = request.form["content"].strip()

            replying_to = None
            attachment_filename = None

            if "replying_to" in request.form:
                replying_to = request.form["replying_to"]

            if "attachment" in request.files:
                attachment = request.files["attachment"]

                attachment_filename = generate_uploads_filename(attachment)

                save_to_uploads(attachment, attachment_filename)

            new_post = Post(
                cat_id=cat_id,
                thread_id=thread_id,
                content=content,
                author=current_user.id,
                replying_to=replying_to,
                attachment_filename=attachment_filename,
            )

            category = Category.query.filter_by(id=cat_id).first()
            thread = Thread.query.filter_by(id=thread_id).first()

            db.session.add(new_post)  # pylint: disable=duplicate-code

            category.last_active_user = current_user.id  # pylint: disable=duplicate-code
            category.last_activity_date = db.func.current_timestamp()  # pylint: disable=duplicate-code

            thread.last_active_user = current_user.id  # pylint: disable=duplicate-code
            thread.last_activity_date = db.func.current_timestamp()  # pylint: disable=duplicate-code

            db.session.commit()  # pylint: disable=duplicate-code

            post_schema = PostSchema()
            result = post_schema.dump(new_post)

            return result

        return form_response(error="Bad request"), 400

    return form_response(error="Unauthorized"), 401


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


@api.put("/posts/<int:post_id>/", strict_slashes=False)
def update_post(post_id: int):
    """Update a post"""

    current_user = authorize(request)
    post = Post.query.filter_by(id=post_id).first()
    author = User.query.filter_by(id=post.author).first()

    if post:
        if not post.deleted:
            if current_user.id == author.id:
                updated = False

                if "content" in request.form:
                    post.content = request.form["content"]
                    updated = True

                if "attachment" in request.files:
                    attachment = request.files["attachment"]

                    if post.attachment_filename:
                        delete_upload(post.attachment_filename)

                    new_attachment_filename = generate_uploads_filename(attachment)

                    post.attachment_filename = new_attachment_filename

                    if len(post.attachment_filename) > 0:
                        save_to_uploads(attachment, post.attachment_filename)

                    updated = True

                if updated:
                    db.session.add(post)
                    db.session.commit()

                    post_schema = PostSchema()

                    result = post_schema.dump(post)

                    return form_response(result)

                return form_response("No changes were made.")

            return form_response(error="Unauthorized"), 401

    return form_response(error="Post not found"), 404


@api.delete("/posts/<int:post_id>/", strict_slashes=False)
def delete_post(post_id: int):
    """Delete a post"""

    current_user = authorize(request)
    post = Post.query.filter_by(id=post_id).first()
    author = User.query.filter_by(id=post.author).first()

    if post:
        if not post.deleted:
            if (
                current_user.role == "admin"
                or (current_user.role == "moderator" and author.role == "user")
                or current_user.id == author.id
            ):
                post.delete()
                db.session.add(post)
                db.session.commit()

                return form_response("Post deleted successfully!")

            return form_response(error="Unauthorized"), 401

    return form_response(error="Post not found"), 404
