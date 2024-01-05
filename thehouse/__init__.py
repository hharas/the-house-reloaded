"""
The House reloaded
"""

import os

from flask import Flask

from .api_routes import api
from .before_request_callbacks import logout_if_deleted, set_default_theme
from .config import Config
from .error_handlers import (handle_method_not_allowed, handle_page_not_found,
                             handle_server_error)
from .extensions import bcrypt, db, ma
from .models import User
from .routes import main
from .user_callbacks import login_manager
from .utils import render_content


def register_blueprints(app):
    """Register blueprints to app"""
    app.register_blueprint(main)
    app.register_blueprint(api)


def create_app(config_class=Config):  # pylint: disable=unused-argument
    """App init function"""
    app = Flask(__name__, static_folder=os.path.join(os.path.pardir, "static"))
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOADS_DIRECTORY"], exist_ok=True)

    if not app.config["SECRET_KEY"]:
        raise ValueError(
            "No app secret key found! Did you set a THR_SECRET_KEY environment variable?"
        )

    login_manager.init_app(app)
    db.init_app(app)
    bcrypt.init_app(app)
    ma.init_app(app)

    register_blueprints(app)

    app.before_request(set_default_theme)
    app.before_request(logout_if_deleted)

    app.errorhandler(404)(handle_page_not_found)
    app.errorhandler(405)(handle_method_not_allowed)
    app.errorhandler(500)(handle_server_error)

    app.jinja_env.filters['render_content'] = render_content

    return app, db
