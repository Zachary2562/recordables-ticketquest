#! usr/bin/python3
# -*- coding: utf-8 -*-
#
# Flicket - copyright Paul Bourne: evereux@gmail.com

from flask import request
from flask import url_for
from flask_babel import lazy_gettext
from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, SubmitField, FileField, DecimalField
from wtforms.fields import SelectMultipleField
from wtforms.validators import DataRequired, Length, ValidationError
from wtforms.widgets import ListWidget, CheckboxInput
from decimal import Decimal

from application.flicket.models.flicket_models import field_size
from application.flicket.models.flicket_models import FlicketCategory
from application.flicket.models.flicket_models import FlicketDepartment
from application.flicket.models.flicket_models import FlicketDepartmentCategory
from application.flicket.models.flicket_models import FlicketPriority
from application.flicket.models.flicket_models import FlicketStatus
from application.flicket.models.flicket_models import FlicketTicket
from application.flicket.models.flicket_user import FlicketUser, user_field_size
from application.flicket.scripts.upload_choice_generator import generate_choices
from application.flicket_admin.models.flicket_config import FlicketConfig
from flask_babel import gettext

form_class_button = {'class': 'btn btn-primary btn-sm'}
form_class_button_sm = {'class': 'btn btn-primary btn-sm'}
form_danger_button = {'class': 'btn btn-danger btn-sm'}


def allowed_file_extension(form, field):
    """
    Check the file extension is in allowed list.
    :param form:
    :param field:
    :return:
    """

    files = request.files.getlist("file")
    valid_extensions = ', '.join(FlicketConfig.valid_extensions())

    if files[0].filename == '':
        return False

    for file in files:
        filename = file.filename

        if filename is not None and '.' not in filename:
            field.errors.append(gettext('"{}" Is not a valid filename.'.format(filename)))
            return False

        if FlicketConfig.extension_allowed(filename):
            return True
        else:
            field.errors.append(gettext('"{}" Is not a an allowed extension. '
                                        'Only the following are currently allowed: "{}"'.format(filename,
                                                                                                valid_extensions)))
            return False

    field.errors.append(gettext('There was a problem with the file attachment.'))
    return False


def does_email_exist(form, field):
    """
    Username must be unique so we check against the database to ensure it doesn't
    :param form:
    :param field:
    :return True / False:
    """
    if form.email.data:
        result = FlicketUser.query.filter_by(email=form.email.data).count()
        if result == 0:
            field.errors.append(gettext('Can\'t find user.'))
            return False
    else:
        return False

    return True


def does_user_exist(form, field):
    """
    Username must be unique so we check against the database to ensure it doesn't
    :param form:
    :param field:
    :return True / False:
    """
    if form.username.data:
        result = FlicketUser.query.filter_by(username=form.username.data).count()
        if result == 0:
            field.errors.append(gettext('Can\'t find user.'))
            return False
    else:
        return False

    return True


def does_department_exist(form, field):
    """
    Username must be unique so we check against the database to ensure it doesn't
    :param form:
    :param field:
    :return True / False:
    """
    result = FlicketDepartment.query.filter_by(department=form.department.data).count()
    if result > 0:
        field.errors.append(gettext('Department already exists.'))
        return False

    return True


def does_category_exist(form, field):
    """
    Username must be unique so we check against the database to ensure it doesn't
    :param form:
    :param field:
    :return True / False:
    """
    result = FlicketCategory.query.filter_by(category=form.category.data).filter_by(
        department_id=form.department_id.data).count()
    if result > 0:
        field.errors.append(gettext('Category already exists.'))
        return False

    return True


def does_unique_department_category_exist(form, field):
    """
    DepartmentCategory is CONCAT of '{FlicketDepartment.department} / {FlicketCategory.category}'
    :param form:
    :param field:
    :return True / False:
    """
    result = FlicketDepartmentCategory.query.filter_by(department_category=form.department_category.data).count()
    if result == 0:
        field.errors.append(gettext('Category does not exist.'))
        return False
    if result > 1:
        field.errors.append(gettext('Ambiguous department / category, contact administrator to fix it!'))
        return False

    return True


def optional_admin_field(form, field):
    """
    Custom validator that only validates if the user is an admin
    """
    from flask import g
    # If user is not admin, don't validate this field
    if not (hasattr(g, 'user') and (g.user.is_admin or g.user.is_super_user)):
        return True
    # If field is empty and user is not admin, that's fine
    if not field.data or field.data == '':
        return True
    # For admin users, validate that the choice is valid
    if field.data not in [choice[0] for choice in field.choices]:
        raise ValidationError('Not a valid choice.')
    return True


class CreateTicketForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        form = super(CreateTicketForm, self).__init__(*args, **kwargs)
        self.priority.choices = [(p.id, p.priority) for p in FlicketPriority.query.all()]
        self.category.choices = [(c.id, "{} - {}".format(c.department.department, c.category)) for c in
                                 FlicketCategory.query.join(FlicketDepartment).order_by(
                                     FlicketDepartment.department).order_by(FlicketCategory.category).all() if
                                 c.department]

    """ Log in form. """
    title = StringField(str(lazy_gettext('username')),
                       validators=[
                           DataRequired(),
                           Length(
                               min=field_size['title_min_length'],
                               max=field_size['title_max_length']
                           )
                       ]
                       )
    content = PageDownField(str(lazy_gettext('content')),
                            validators=[DataRequired(), Length(min=field_size['content_min_length'],
                                                               max=field_size['content_max_length'])])
    priority = SelectField(str(lazy_gettext('priority')), validators=[DataRequired()], coerce=int)
    category = SelectField(str(lazy_gettext('category')), validators=[DataRequired()], coerce=int)
    file = FileField(str(lazy_gettext('Upload Documents')),
                     validators=[allowed_file_extension],
                     render_kw={'multiple': True}
                     )
    hours = DecimalField(str(lazy_gettext('hours')), default=Decimal('0'))
    submit = SubmitField(str(lazy_gettext('Submit')), render_kw=form_class_button, validators=[DataRequired()])


class MultiCheckBoxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class EditTicketForm(CreateTicketForm):
    def __init__(self, ticket_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # get ticket data from ticket_id
        ticket = FlicketTicket.query.filter_by(id=ticket_id).first()

        # define the multi select box for document uploads
        uploads = []
        for u in ticket.uploads:
            uploads.append((u.id, u.filename, u.original_filename))
        self.uploads.choices = []
        for x in uploads:
            uri = url_for('flicket_bp.view_ticket_uploads', filename=x[1])
            uri_label = '<a href="' + uri + '">' + x[2] + '</a>'
            self.uploads.choices.append((x[0], uri_label))

    uploads = MultiCheckBoxField('Label', coerce=int)
    submit = SubmitField(str(lazy_gettext('Edit Ticket')), render_kw=form_class_button, validators=[DataRequired()])


class ReplyForm(FlaskForm):
    """ Content form. Displayed when replying too end editing tickets """

    def __init__(self, *args, **kwargs):
        form = super(ReplyForm, self).__init__(*args, **kwargs)
        # Add empty choice for non-admin users
        status_choices = [('', 'Select Status')] + [(s.id, s.status) for s in FlicketStatus.query.filter(FlicketStatus.status != 'Closed')]
        priority_choices = [('', 'Select Priority')] + [(p.id, p.priority) for p in FlicketPriority.query.all()]
        
        self.status.choices = status_choices
        self.priority.choices = priority_choices

    content = PageDownField(str(lazy_gettext('Reply')),
                            validators=[DataRequired(), Length(min=field_size['content_min_length'],
                                                               max=field_size['content_max_length'])])
    file = FileField(str(lazy_gettext('Add Files')), validators=[allowed_file_extension], render_kw={'multiple': True})
    status = SelectField(str(lazy_gettext('Status')), validators=[optional_admin_field], default='')  # Custom validator for admin-only
    priority = SelectField(str(lazy_gettext('Priority')), validators=[optional_admin_field], default='')  # Custom validator for admin-only
    hours = DecimalField(str(lazy_gettext('hours')), default=Decimal('0'))
    submit = SubmitField(str(lazy_gettext('reply')), render_kw=form_class_button)
    submit_close = SubmitField(str(lazy_gettext('reply and close')), render_kw=form_danger_button)


class EditReplyForm(ReplyForm):
    def __init__(self, post_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = generate_choices('Post', id=post_id)
        self.uploads.choices = choices if choices is not None else []

    uploads = MultiCheckBoxField('Label', coerce=int)
    submit = SubmitField(str(lazy_gettext('Edit Reply')), render_kw=form_class_button, validators=[DataRequired()])


class SearchUserForm(FlaskForm):
    """ Search user. """
    username = StringField(str(lazy_gettext('username')),
                           validators=[
                               DataRequired(),
                               Length(min=user_field_size['username_min'], max=user_field_size['username_max']),
                               does_user_exist
                           ]
                           )
    submit = SubmitField(str(lazy_gettext('find user')), render_kw=form_class_button)


class AssignUserForm(FlaskForm):
    """ Assign user form with dropdown. """
    username = SelectField(str(lazy_gettext('username')),
                          validators=[DataRequired()],
                          choices=[])
    
    def __init__(self, *args, **kwargs):
        super(AssignUserForm, self).__init__(*args, **kwargs)
        # Dynamically populate choices with admin users
        from application.flicket.models.flicket_user import FlicketUser
        from application import app
        
        # Get all users who are admins
        admin_users = []
        for user in FlicketUser.query.all():
            if user.is_admin:
                admin_users.append((user.username, user.name))
        
        # Add a default option
        self.username.choices = [('', 'Select an admin user...')] + admin_users
    
    submit = SubmitField(str(lazy_gettext('assign user')), render_kw=form_class_button)


class SubscribeUser(SearchUserForm):
    """ Search user. """

    sub_user = SubmitField(str(lazy_gettext('subscribe user')), render_kw=form_class_button)


class UnSubscribeUser(FlaskForm):
    """ Search user. """
    username = HiddenField(str(lazy_gettext('username')), validators=[DataRequired()])
    unsub_user = SubmitField(str(lazy_gettext('Unsubscribe user')), render_kw=form_class_button)


class DepartmentForm(FlaskForm):
    """ Department form. """
    department = StringField(str(lazy_gettext('Department')),
                             validators=[DataRequired(), Length(min=field_size['department_min_length'],
                                                                max=field_size['department_max_length']),
                                         does_department_exist])
    submit = SubmitField(str(lazy_gettext('add department')), render_kw=form_class_button)


class CategoryForm(FlaskForm):
    """ Category form. """
    category = StringField(str(lazy_gettext('Category')),
                           validators=[DataRequired(), Length(min=field_size['category_min_length'],
                                                              max=field_size['category_max_length']),
                                       does_category_exist])
    department_id = HiddenField('department_id')
    submit = SubmitField(str(lazy_gettext('add category')), render_kw=form_class_button)


class SearchDepartmentCategoryForm(FlaskForm):
    """ Search department / category. """
    department_category = StringField(str(lazy_gettext('Department / Category')),
                                      validators=[DataRequired(), does_unique_department_category_exist])
    submit = SubmitField(str(lazy_gettext('search department / category')), render_kw=form_class_button)


class ChangeDepartmentCategoryForm(SearchDepartmentCategoryForm):
    """ Change department / category. """
    submit = SubmitField(str(lazy_gettext('change department / category')), render_kw=form_class_button)
