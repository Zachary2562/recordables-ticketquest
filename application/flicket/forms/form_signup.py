from flask_wtf import FlaskForm
from flask_babel import lazy_gettext
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from application.flicket.models.flicket_user import FlicketUser

class SignUpForm(FlaskForm):
    username = StringField(lazy_gettext('Username'), validators=[DataRequired()])
    name = StringField(lazy_gettext('Full Name'), validators=[DataRequired()])
    email = StringField(lazy_gettext('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(lazy_gettext('Password'), validators=[DataRequired()])
    confirm_password = PasswordField(lazy_gettext('Confirm Password'), validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField(lazy_gettext('Sign Up'))

    def validate_username(self, field):
        if FlicketUser.query.filter_by(username=field.data).first():
            raise ValidationError('Username already exists.')

    def validate_email(self, field):
        if FlicketUser.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.') 