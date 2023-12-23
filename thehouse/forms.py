"""
The House reloaded
Form definitions
"""

from flask_wtf import FlaskForm
from wtforms import (FileField, PasswordField, StringField, SubmitField,
                     TextAreaField)
from wtforms.validators import InputRequired, Length, ValidationError

from .extensions import bcrypt
from .models import Category, User


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
