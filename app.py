"""
The House reloaded
"""

import os
import sys
from typing import List, Optional
from uuid import uuid4

import bleach
from dotenv import load_dotenv
from flask import (Flask, redirect, render_template, request,
                   send_from_directory, session, url_for)
from flask_bcrypt import Bcrypt
from flask_login import (LoginManager, UserMixin, current_user, login_user,
                         logout_user)
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import (FileField, PasswordField, StringField, SubmitField,
                     TextAreaField)
from wtforms.validators import InputRequired, Length, ValidationError

load_dotenv()


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
        app.config["UPLOADS_DIRECTORY"], attachment_filename))


def render_content(value: str) -> str:
    """Turn thread/post contents into renderable HTML"""
    cleaned = bleach.clean(value)
    linkified = bleach.linkify(cleaned, parse_email=True)
    nl2brd = linkified.replace('\n', "<br />")

    return nl2brd


app = Flask(__name__)
app.config["SITE_NAME"] = os.getenv("THR_SITE_NAME") or "The House"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "THR_DATABASE_URI") or "sqlite:///thehouse.db"
app.config["SECRET_KEY"] = os.getenv("THR_SECRET_KEY")
app.config["STATIC_DIRECTORY"] = os.getenv("THR_STATIC_DIRECTORY") or "static"
app.config["UPLOADS_DIRECTORY"] = os.getenv(
    "THR_UPLOADS_DIRECTORY") or "uploads"
app.config["ENABLE_ADMIN_KEY"] = os.getenv("THR_ENABLE_ADMIN_KEY") == "yes"
app.config["ADMIN_KEY"] = None if not app.config["ENABLE_ADMIN_KEY"] else os.getenv(
    "THR_ADMIN_KEY")
app.config["PREVIEWABLE_EXTENSIONS"] = ["png", "jpeg", "jpg", "webp", "gif",
                                        "mp4", "webm", "mp3", "ogg", "wav",
                                        "flac", "alac", "m4a", "aac", "svg"]
app.jinja_env.filters['render_content'] = render_content

if not app.config["SECRET_KEY"]:
    eprint("No app secret key found! Did you set a THR_SECRET_KEY environment variable?")
    sys.exit(1)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

bcrypt = Bcrypt(app)
os.makedirs(app.config["UPLOADS_DIRECTORY"], exist_ok=True)


def delete_upload(filename: str):
    """Delete an uploaded file"""
    try:
        os.remove(os.path.join(
            app.config["UPLOADS_DIRECTORY"], filename))
    except FileNotFoundError as error:
        eprint(error)


@login_manager.user_loader
def load_user(user_id):
    """Callback function for loading users from the database"""
    return User.query.get(str(user_id))


@app.before_request
def set_default_theme():
    """Load the light theme by default if there's no set theme"""
    if "theme" not in session:
        session["theme"] = "light"


@app.before_request
def logout_if_deleted():
    """Logout a user if his account has been deleted"""
    if current_user.is_authenticated:
        if current_user.deleted:
            logout_user()


db = SQLAlchemy(app)
Migrate(app, db)


class User(db.Model, UserMixin):  # pylint: disable=too-few-public-methods
    """A Housean user"""
    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid4()), unique=True)
    token = db.Column(db.String(36),
                      default=lambda: str(uuid4()), unique=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    joined_date = db.Column(db.DateTime, nullable=False,
                            server_default=db.func.current_timestamp())
    role = db.Column(db.Enum("admin", "moderator", "user",
                     name='user_roles'), default="user")
    picture_filename = db.Column(db.Text)
    bio = db.Column(db.String(60))
    deleted = db.Column(db.Boolean, nullable=False, default=False)

    def delete(self):
        """Demote the user and flag him as deleted"""

        self.deleted = True
        self.role = "user"

        if self.picture_filename:
            delete_upload(self.picture_filename)


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
        db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    views = db.Column(db.Integer, nullable=False, default=0)
    deleted = db.Column(db.Boolean, nullable=False, default=False)

    def delete(self):
        """Remove thread contents and flag it as deleted"""

        self.deleted = True
        self.title = ""
        self.content = ""

        if self.attachment_filename:
            delete_upload(self.attachment_filename)


class Post(db.Model):  # pylint: disable=too-few-public-methods
    """A post on the House"""
    id = db.Column(db.Integer, primary_key=True)
    cat_id = db.Column(db.Integer, nullable=False)
    thread_id = db.Column(db.Integer, nullable=False)
    author = db.Column(db.String(36), nullable=False)
    content = db.Column(db.Text, nullable=False)
    creation_date = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    replying_to = db.Column(db.Integer)
    attachment_filename = db.Column(db.Text)
    deleted = db.Column(db.Boolean, nullable=False, default=False)

    def delete(self):
        """Remove post contents and flag it as deleted"""
        self.deleted = True
        self.content = ""

        if self.attachment_filename:
            delete_upload(self.attachment_filename)


class RegisterForm(FlaskForm):
    """Registration form class"""
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)])
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=300)])
    submit = SubmitField("register")

    def validate_username(self, field):
        """Making sure the username isn't already registered"""
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("That username already exists")

        if ' ' in field.data:
            raise ValidationError("Username contains spaces")


class LoginForm(FlaskForm):
    """Registration form class"""
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)])
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=300)])
    submit = SubmitField("login")

    def validate_username(self, field):
        """Make sure the entered username exists"""
        if not User.query.filter_by(username=field.data):
            raise ValidationError("Username not found")

    def validate_password(self, field):
        """Make sure the password is correct"""
        username = self.username.data

        user = User.query.filter_by(username=username).first()

        if user:
            if user.deleted:
                raise ValidationError("This account has been deleted")

            if not bcrypt.check_password_hash(user.password, field.data):
                raise ValidationError("Incorrect password")


class CreateCategoryForm(FlaskForm):
    """New Category form class"""
    title = StringField(validators=[InputRequired(), Length(
        min=2, max=20)])
    description = StringField(validators=[InputRequired(), Length(
        min=2, max=100)])
    submit = SubmitField("create")

    def validate_title(self, field):
        """Make sure the new title isn't used"""
        if Category.query.filter_by(title=field.data).first():
            raise ValidationError("Title must be unique")

        if ' ' in field.data:
            raise ValidationError("Title contains spaces")


class CreateThreadForm(FlaskForm):
    """New Thread form class"""
    title = StringField(validators=[InputRequired(), Length(
        min=2, max=255)])
    content = TextAreaField()
    file = FileField()
    submit = SubmitField("create")


class CreatePostForm(FlaskForm):
    """New post form class"""
    content = TextAreaField()
    file = FileField()
    submit = SubmitField("post your reply")

    def validate_content(self, field):
        """Make sure the comment is not empty"""
        content = field.data
        file = self.file.data

        if not content and not file:
            raise ValidationError("Empty post")


@app.get('/')
def index():
    """Homepage"""

    categories = Category.query.all()

    for category in categories:
        category.activities = []

        for thread in Thread.query.filter_by(cat_id=category.id):
            if not thread.deleted:
                if not User.query.filter_by(id=thread.creator).first().deleted:
                    category.activities.append(
                        {"type": "thread", "data": thread})
        for post in Post.query.filter_by(cat_id=category.id):
            if not post.deleted:
                if not User.query.filter_by(id=post.author).first().deleted:
                    category.activities.append({"type": "post", "data": post})

        category.activities = sorted(
            category.activities,
            key=lambda activity: activity['data'].creation_date,
        )

    return render_template(
        "index.html",
        categories=categories,
        Thread=Thread,
        Post=Post,
        User=User,
    )


@app.get("/promote")
def promote():
    """Endpoint that promotes a user to admin if he has an admin key"""
    if current_user.is_authenticated:
        if app.config["ENABLE_ADMIN_KEY"]:
            if app.config["ADMIN_KEY"] is not None:
                if request.args.get("key") == app.config["ADMIN_KEY"]:
                    user = User.query.filter_by(id=current_user.id).first()
                    user.role = "admin"

                    db.session.add(user)
                    db.session.commit()

                    return redirect(url_for("index"))

                return render_template("403.html"), 403

    return render_template("404.html"), 404


@app.get("/toggle-theme")
def toggle_theme():
    """Endpoint for theme toggling"""

    session["theme"] = "dark" if session["theme"] == "light" else "light"

    return redirect(request.referrer) if request.referrer is not None \
        else redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""

    login_form = LoginForm()
    register_form = RegisterForm()

    if login_form.validate_on_submit():
        user = User.query.filter_by(username=login_form.username.data).first()

        if user:
            login_user(user)

            return redirect(request.args.get("referer", url_for("index")))

    if register_form.validate_on_submit():
        if db.engine.dialect.name == "postgresql":
            hashed_password = bcrypt.generate_password_hash(
                register_form.password.data
            ).decode("utf-8")

        elif db.engine.dialect.name == "sqlite":
            hashed_password = bcrypt.generate_password_hash(
                register_form.password.data
            )

        new_user = User(username=register_form.username.data,
                        password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        return redirect(request.args.get("referer", url_for("index")))

    if current_user.is_authenticated:
        return redirect(request.referrer) if request.referrer is not None \
            else redirect(url_for("index"))

    return render_template(
        "login.html",
        login_form=login_form,
        register_form=register_form
    )


@app.get("/logout")
def logout():
    """Logout functionality"""

    logout_user()

    return redirect(request.referrer) if request.referrer is not None \
        else redirect(url_for("index"))


@app.route("/settings", methods=["GET", "POST"])
def settings():
    """Account settings page"""

    if not current_user.is_authenticated:
        return render_template("404.html"), 404

    class SettingsForm(FlaskForm):
        """Settings form class"""
        bio = StringField(
            validators=[Length(min=0, max=60)], default=current_user.bio)
        profile_picture_file = FileField()

        submit = SubmitField("save")

    form = SettingsForm()

    if form.validate_on_submit():
        user = User.query.filter_by(id=current_user.id).first()
        profile_picture_filename = ""

        if form.bio.data != current_user.bio:
            user.bio = form.bio.data.strip(
            ) if form.bio.data.strip() != "" else None
            db.session.add(user)

        if form.profile_picture_file.data:
            if user.picture_filename:
                delete_upload(user.picture_filename)

            profile_picture_filename = generate_uploads_filename(
                form.profile_picture_file.data)

            user.picture_filename = profile_picture_filename
            db.session.add(user)

        db.session.commit()

        if len(profile_picture_filename) > 0:
            save_to_uploads(
                form.profile_picture_file.data, profile_picture_filename)

        return redirect(request.args.get("referer", url_for("index")))

    return render_template(
        "settings.html",
        form=form,
    )


@app.get("/about")
def about():
    """About page"""

    return render_template("about.html")


@app.get("/~<username>")
def view_user(username: str):
    """View for viewing user profile"""

    user = User.query.filter_by(username=username).first()

    if user:
        if not user.deleted:
            activities = []

            for thread in Thread.query.filter_by(creator=user.id).all():
                if not thread.deleted:
                    activities.append({"type": "thread", "data": thread})

            for post in Post.query.filter_by(author=user.id).all():
                if not post.deleted:
                    activities.append({"type": "post", "data": post})

            activities = sorted(
                activities,
                key=lambda activity: activity['data'].creation_date,
                reverse=True
            )

            return render_template(
                "view-user.html",
                user=user,
                activities=activities,
                Category=Category,
                Thread=Thread,
            )

    return render_template("404.html"), 404


@app.route("/new", methods=["GET", "POST"])
def create_category():
    """Create category page"""

    form = CreateCategoryForm()

    if form.validate_on_submit():
        new_category = Category(title=form.title.data,
                                description=form.description.data)
        db.session.add(new_category)
        db.session.commit()

        return redirect(url_for("index"))

    if current_user.is_authenticated:
        if current_user.role == "admin":
            return render_template("new-category.html", form=form)

        return render_template("403.html"), 403

    return render_template("404.html"), 404


@app.route("/<cat_title>/", strict_slashes=False)
def view_category(cat_title: str):
    """View for viewing a category"""

    category = Category.query.filter_by(title=cat_title).first()

    if category:
        threads = Thread.query.filter_by(
            cat_id=category.id, deleted=False).all()

        for thread in threads:
            thread.posts = []

            for post in Post.query.filter_by(thread_id=thread.id):
                if not post.deleted:
                    if not User.query.filter_by(id=post.author).first().deleted:
                        thread.posts.append(post)

            thread.posts = sorted(
                thread.posts,
                key=lambda post: post.creation_date,
            )

        return render_template(
            "view-category.html",
            category=category,
            threads=threads,
            User=User,
            Post=Post
        )

    return render_template("404.html"), 404


@app.route("/<cat_title>/new", methods=["GET", "POST"])
def create_thread(cat_title: str):
    """Create thread page"""

    category = Category.query.filter_by(title=cat_title).first()

    form = CreateThreadForm()

    if form.validate_on_submit():
        form.content.data = form.content.data.strip()

        if form.file.data:
            attachment_filename = generate_uploads_filename(form.file.data)

            new_thread = Thread(
                cat_id=category.id,
                title=form.title.data,
                content=form.content.data,
                creator=current_user.id,
                attachment_filename=attachment_filename
            )
        else:
            attachment_filename = None
            new_thread = Thread(
                cat_id=category.id,
                title=form.title.data,
                content=form.content.data,
                creator=current_user.id,
            )

        db.session.add(new_thread)
        category.last_active_user = current_user.id
        category.last_activity_date = db.func.current_timestamp()
        db.session.commit()

        if attachment_filename:
            save_to_uploads(form.file.data, attachment_filename)

        return redirect(url_for("view_thread", cat_title=category.title, thread_id=new_thread.id))

    if current_user.is_authenticated:
        return render_template(
            "new-thread.html",
            form=form,
            category=category
        )

    return render_template("403.html"), 403


@app.route("/<cat_title>/<int:thread_id>/new", methods=["GET", "POST"])
def create_post(cat_title: str, thread_id: int):
    """View for posting a comment inside a thread"""

    category = Category.query.filter_by(title=cat_title).first()
    thread = Thread.query.filter_by(id=thread_id).first()
    reply_to = request.args.get("reply_to")

    form = CreatePostForm()

    if form.validate_on_submit():
        if form.file.data:
            attachment_filename = generate_uploads_filename(
                form.file.data)

            new_post = Post(
                cat_id=category.id,
                thread_id=thread.id,
                content=form.content.data,
                author=current_user.id,
                replying_to=reply_to,
                attachment_filename=attachment_filename
            )
        else:
            attachment_filename = None

            new_post = Post(
                cat_id=category.id,
                thread_id=thread.id,
                content=form.content.data,
                author=current_user.id,
                replying_to=reply_to,
            )

        db.session.add(new_post)

        category.last_active_user = current_user.id
        category.last_activity_date = db.func.current_timestamp()

        thread.last_active_user = current_user.id
        thread.last_activity_date = db.func.current_timestamp()

        db.session.commit()

        if attachment_filename:
            save_to_uploads(form.file.data, attachment_filename)

        return redirect(
            url_for(
                "view_thread",
                cat_title=category.title,
                thread_id=thread_id
            ) + '#' + str(new_post.id)
        )

    if current_user.is_authenticated:
        if reply_to is not None:
            replied_to = Post.query.filter_by(id=reply_to).first()

            if not replied_to or \
                    (
                        category.id != replied_to.cat_id or
                        thread_id != replied_to.thread_id
                    ) or replied_to.deleted:
                return render_template("404.html"), 404

        if thread.deleted:
            return render_template("404.html"), 404

        return render_template(
            "new-post.html",
            form=form,
            category=category,
            thread=thread,
            User=User,
            Post=Post,
            reply_to=reply_to
        )

    return render_template("403.html"), 403


@app.get("/<cat_title>/<int:thread_id>/", strict_slashes=False)
def view_thread(cat_title: str, thread_id: int):
    """View for viewing a thread"""

    def build_tree(posts: List[Post], parent_id: Optional[int] = None) -> str:
        """Build post tree in view_thread()"""
        html = ""

        for post in posts:
            author = User.query.filter_by(id=post.author).first()
            category = Category.query.filter_by(id=post.cat_id).first()

            author_post_count = len(
                Post.query.filter_by(author=author.id).all())
            author_profile_url = url_for("view_user", username=author.username)

            if author.role == "user":
                author_rendered_role = f"""<span style="color: lightgreen;">{author.role}</span>"""
            elif author.role == "moderator":
                author_rendered_role = f"""<span style="color: yellow;">{author.role}</span>"""
            else:
                author_rendered_role = f"""<span style="color: red;">{author.role}</span>"""

            picture_url = url_for(
                "uploads",
                filename=author.picture_filename
            ) if author.picture_filename else \
                url_for(
                "static",
                filename="default.png"
            )
            post_url = url_for(
                'view_thread',
                cat_title=category.title,
                thread_id=post.thread_id
            ) + '#' + str(post.id)
            reply_url = url_for(
                'create_post',
                cat_title=category.title,
                thread_id=post.thread_id
            ) + "?reply_to=" + str(post.id)

            if post.replying_to == parent_id:
                html += f"""<div id="{post.id}" class="comment">
            <div class="top-comment">
            <div class="tooltip-wrap">"""

                if author.deleted:
                    html += """<p style="color: #808080; font-style: italic;">[deleted]</p></div>"""
                else:
                    html += f"""<a
                    style="color: #808080"
                    href="{author_profile_url}"
                    >{author.username}</a
                    >
                    <div class="tooltip-content">
                    <p>
                        <a href="{author_profile_url}"
                        >{author.username}</a
                        >
                        | {author_rendered_role} | {author_post_count} posts
                    </p>"""

                    if author.bio:
                        html += f"""<p style="color: #808080; font-size: 13px">Bio:</p>
                    <p class="bio">{author.bio}</p>"""

                    html += f"""
                            <img
                                src="{picture_url}"
                                style="max-width: 160px; margin-top: 3px"
                            />
                            </div>
                        </div>"""

                html += f"""<p class="comment-tr">
                        <a
                        style="color: #808080"
                        href="{post_url}"
                        >
                        {post.creation_date}
                        </a>
                    </p>"""

                if current_user.is_authenticated and not post.deleted:
                    html += f"""
                    <p class="comment-tr">
                        <a
                        href="{reply_url}"
                        >[reply]</a
                        >
                    </p>
                    """

                    if post.attachment_filename and not post.deleted:
                        html += f"""<p class="comment-tr">
                        <a href="{url_for("uploads", filename=post.attachment_filename) + "?download=true"}">[save]</a>
                        </p>"""

                    if not post.deleted and (current_user.role == "admin" or
                                             (
                                                 current_user.role == "moderator" and
                                                 author.role == "user"
                                             ) or
                                             current_user.id == post.author):
                        html += f"""<p class="comment-tr">
                                    <a href="{url_for('delete_post', cat_title=category.title, thread_id=post.thread_id, post_id=post.id)}">[delete]</a>
                                </p>"""

                elif post.attachment_filename and not post.deleted:
                    html += f"""<p class="comment-tr">
                    <a href="{url_for("uploads", filename=post.attachment_filename) + "?download=true"}">[save]</a>
                    </p>"""

                html += "</div>"

                if post.deleted:
                    html += """<div class="comment-content" style="font-style: italic;"
                        >[deleted]
                    </div>"""

                if post.content:
                    html += f"""<div class="comment-content">{render_content(post.content)}</div>"""

                if post.attachment_filename and not post.deleted:
                    attachment_url = url_for(
                        'uploads', filename=post.attachment_filename)
                    if post.attachment_filename.split('.')[-1] in \
                            app.config["PREVIEWABLE_EXTENSIONS"]:
                        html += f"""<embed
                            src="{attachment_url}"
                            style="max-height: 300px; margin-top: 5px"
                            />"""
                    else:
                        html += f"""
                        <a href="{attachment_url}"
                            >{post.attachment_filename}</a
                            >"""

                child_html = build_tree(posts, post.id)
                if child_html.strip():
                    html += """<div class="comment-children">"""
                    html += child_html
                    html += "</div>"

                html += "</div>"

        return html

    category = Category.query.filter_by(title=cat_title).first()
    thread = Thread.query.filter_by(id=thread_id).first()
    posts = Post.query.filter_by(thread_id=thread_id).all()
    rendered_posts = build_tree(posts)
    form = CreatePostForm()

    if category:
        if thread:
            thread.views += 1
            db.session.commit()

            return render_template(
                "view-thread.html",
                form=form,
                category=category,
                thread=thread,
                rendered_posts=rendered_posts,
                User=User,
                Post=Post
            )

    return render_template("404.html"), 404


@app.get("/<cat_title>/<int:thread_id>/<int:post_id>/delete")
def delete_post(cat_title: str, thread_id: int, post_id: int):
    """View for deleting a post"""

    category = Category.query.filter_by(title=cat_title).first()
    thread = Thread.query.filter_by(id=thread_id).first()
    post = Post.query.filter_by(id=post_id).first()
    author = User.query.filter_by(id=post.author).first()

    if post.cat_id == category.id and post.thread_id == thread.id:
        if not post.deleted:
            if current_user.is_authenticated:
                if current_user.role == "admin" or \
                    (current_user.role == "moderator" and author.role == "user") or \
                        current_user.id == author.id:
                    if request.args.get("confirm") == "yes":
                        post.delete()
                        db.session.add(post)
                        db.session.commit()

                        return redirect(
                            url_for(
                                "view_thread",
                                cat_title=category.title,
                                thread_id=thread.id
                            ) + '#' + str(post.id)
                        )

                    return render_template(
                        "delete-post.html",
                        category=category,
                        thread=thread,
                        post=post,
                        author=author
                    )

            return render_template("403.html"), 403

    return render_template("404.html"), 404


@app.get("/<cat_title>/<int:thread_id>/delete")
def delete_thread(cat_title: str, thread_id: int):
    """View for deleting a thread"""

    category = Category.query.filter_by(title=cat_title).first()
    thread = Thread.query.filter_by(id=thread_id).first()
    creator = User.query.filter_by(id=thread.creator).first()

    if thread.cat_id == category.id:
        if not thread.deleted:
            if current_user.is_authenticated:
                if current_user.role == "admin" or \
                    (current_user.role == "moderator" and creator.role == "user") or \
                        current_user.id == creator.id:
                    if request.args.get("confirm") == "yes":
                        for post in Post.query.filter_by(thread_id=thread.id).all():
                            post.delete()
                            db.session.add(post)

                        thread.delete()
                        db.session.add(thread)
                        db.session.commit()

                        return redirect(
                            url_for(
                                "view_thread",
                                cat_title=category.title,
                                thread_id=thread.id
                            )
                        )

                    return render_template(
                        "delete-thread.html",
                        category=category,
                        thread=thread,
                        posts=Post.query.filter_by(thread_id=thread.id).all()
                    )

            return render_template("403.html"), 403

    return render_template("404.html"), 404


@app.get("/<cat_title>/delete")
def delete_category(cat_title: str):
    """View for deleting a category"""

    category = Category.query.filter_by(title=cat_title).first()
    threads = Thread.query.filter_by(cat_id=category.id).all()
    posts = Post.query.filter_by(cat_id=category.id).all()

    if not category.deleted:
        if current_user.is_authenticated:
            if current_user.role == "admin":
                if request.args.get("confirm") == "yes":
                    for post in posts:
                        if not post.deleted:
                            post.delete()
                            db.session.add(post)

                    for thread in threads:
                        if not thread.deleted:
                            thread.delete()
                            db.session.add(thread)

                    category.delete()
                    db.session.add(category)

                    db.session.commit()

                    return redirect(url_for("index"))

                return render_template(
                    "delete-category.html",
                    category=category,
                    threads=threads,
                    posts=posts
                )

            return render_template("403.html"), 403

    return render_template("404.html"), 404


@app.get("/~<username>/delete")
def delete_user(username: str):
    """View for deleting a user"""

    user = User.query.filter_by(username=username).first()
    threads = Thread.query.filter_by(creator=user.id).all()
    posts = Post.query.filter_by(author=user.id).all()

    if not user.deleted:
        if current_user.is_authenticated:
            if current_user.role == "admin" or \
                    current_user.id == user.id:
                if request.args.get("confirm") == "yes":
                    for post in posts:
                        if not post.deleted:
                            post.delete()
                            db.session.add(post)

                    for thread in threads:
                        if not thread.deleted:
                            thread.delete()
                            db.session.add(thread)

                    user.delete()
                    db.session.add(user)

                    db.session.commit()

                    if current_user.id == user.id:
                        logout_user()

                    return redirect(url_for("index"))

                return render_template(
                    "delete-user.html",
                    user=user,
                    threads=threads,
                    posts=posts,
                )

            return render_template("403.html"), 403

    return render_template("404.html"), 404


@app.get("/up/<path:filename>")
def uploads(filename: str):
    """Serve uploaded files"""

    if not os.path.exists(os.path.join(app.config["UPLOADS_DIRECTORY"], filename)):
        return redirect(url_for("static", filename="filenotfound.jpg"))

    if request.args.get("download") == "true":
        return send_from_directory(app.config["UPLOADS_DIRECTORY"], filename, as_attachment=True)

    return send_from_directory(app.config["UPLOADS_DIRECTORY"], filename)


@app.errorhandler(404)
def pagenotfound(_):
    """Handle viewing a non-existent page"""

    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run()
