#! usr/bin/python3
# -*- coding: utf8 -*-
#
# Flicket - copyright Paul Bourne: evereux@gmail.com

import datetime
import os

from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import make_response
from flask import Response
from flask_babel import gettext
from flask_login import current_user
from flask_login import login_required
from flask_principal import identity_loaded
from flask_principal import Permission
from flask_principal import Principal
from flask_principal import RoleNeed
from flask_principal import UserNeed

from application import app, db
from application.flicket.models.flicket_user import FlicketUser
from application.flicket.models.flicket_user import FlicketGroup
from application.flicket.models.flicket_models import FlicketTicket, FlicketPriority, FlicketStatus, FlicketUploads, FlicketPost, FlicketHistory
from application.flicket.forms.search import SearchTicketForm
from application.flicket.scripts.hash_password import hash_password
from application.flicket_admin.forms.forms_admin import AddGroupForm, AddUserForm, EnterPasswordForm, EditUserForm, PriorityForm, StatusForm
from application.flicket.forms.forms_main import ConfirmPassword
from . import admin_bp

# Import the Mock classes from flicket views
from application.flicket.views.index import MockTicket, MockUser, MockCategory, MockDepartment, MockPriority, MockStatus

principals = Principal(app)
# define flicket_admin role need
admin_only = RoleNeed('flicket_admin')
admin_permission = Permission(admin_only)


def clean_csv_data(input_text):
    output_text = input_text.replace('"', "'")
    return output_text


def admin_tickets_view(page):
    """
        Admin tickets view function - same as regular tickets but with admin permissions.
    """

    form = SearchTicketForm()

    # get request arguments from the url
    status = request.args.get('status')
    department = request.args.get('department')
    category = request.args.get('category')
    content = request.args.get('content')
    user_id = request.args.get('user_id')
    assigned_id = request.args.get('assigned_id')
    created_id = request.args.get('created_id')

    if form.validate_on_submit():
        redirect_url = FlicketTicket.form_redirect(form, url='admin_bp.tickets')
        return redirect(redirect_url)

    arg_sort = request.args.get('sort')
    if arg_sort:
        args = request.args.copy()
        del args['sort']
        filtered_args = {k: v for k, v in args.items() if k not in ['_external', '_scheme', '_anchor']}
        if '_external' in filtered_args:
            del filtered_args['_external']
        response = make_response(redirect(url_for('admin_bp.tickets', **filtered_args)))  # type: ignore
        response.set_cookie('admin_tickets_sort', arg_sort, max_age=2419200, path=app.config['ADMINHOME'] + 'tickets/')
        return response

    sort = request.cookies.get('admin_tickets_sort')
    if sort:
        set_cookie = True
    else:
        sort = 'priority_desc'
        set_cookie = False

    # Create a simple pagination object
    class SimplePagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            
        def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
            last = 0
            for num in range(1, self.pages + 1):
                if num <= left_edge or (num > self.page - left_current - 1 and num < self.page + right_current) or num > self.pages - right_edge:
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num
                    
        @property
        def has_prev(self):
            return self.page > 1
            
        @property
        def has_next(self):
            return self.page < self.pages
            
        @property
        def prev_num(self):
            return self.page - 1 if self.has_prev else None
            
        @property
        def next_num(self):
            return self.page + 1 if self.has_next else None

    # Use raw SQL to avoid datetime parsing issues
    try:
        # Build the base SQL query
        sql_query = """
            SELECT t.id, t.title, t.content, t.date_added, 
                   u.name as user_name, d.department as dept_name, c.category as cat_name,
                   p.priority as priority_name, s.status as status_name,
                   au.name as assigned_name,
                   (SELECT COUNT(*) FROM flicket_post WHERE ticket_id = t.id) as num_replies,
                   t.hours
            FROM flicket_topic t
            LEFT JOIN flicket_users u ON t.started_id = u.id
            LEFT JOIN flicket_category c ON t.category_id = c.id
            LEFT JOIN flicket_department d ON c.department_id = d.id
            LEFT JOIN flicket_priorities p ON t.ticket_priority_id = p.id
            LEFT JOIN flicket_status s ON t.status_id = s.id
            LEFT JOIN flicket_users au ON t.assigned_id = au.id
            WHERE 1=1
        """
        
        # Add filters
        if status:
            sql_query += f" AND s.status = '{status}'"
        if department:
            sql_query += f" AND d.department = '{department}'"
        if category:
            sql_query += f" AND c.category = '{category}'"
        if user_id:
            sql_query += f" AND t.started_id = {user_id}"
        if assigned_id:
            sql_query += f" AND t.assigned_id = {assigned_id}"
        if created_id:
            sql_query += f" AND t.started_id = {created_id}"
        if content:
            sql_query += f" AND (t.title LIKE '%{content}%' OR t.content LIKE '%{content}%')"
            
        # Add sorting
        if sort == 'priority_desc':
            sql_query += " ORDER BY p.id DESC, t.id DESC"
        elif sort == 'priority_asc':
            sql_query += " ORDER BY p.id ASC, t.id DESC"
        elif sort == 'date_desc':
            sql_query += " ORDER BY t.date_added DESC"
        elif sort == 'date_asc':
            sql_query += " ORDER BY t.date_added ASC"
        elif sort == 'title_asc':
            sql_query += " ORDER BY t.title ASC"
        elif sort == 'title_desc':
            sql_query += " ORDER BY t.title DESC"
        else:
            sql_query += " ORDER BY t.id DESC"
            
        # Execute the query
        result = db.session.execute(sql_query)
        all_tickets = [MockTicket(dict(row)) for row in result]
        
        # Calculate total count
        number_results = len(all_tickets)
        
        # Manual pagination
        per_page = app.config['posts_per_page']
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        ticket_query = all_tickets[start_idx:end_idx]
        
        ticket_query = SimplePagination(ticket_query, page, per_page, number_results)
        
    except Exception as e:
        print(f"Error querying admin tickets: {e}")
        # Fallback to empty results
        number_results = 0
        ticket_query = SimplePagination([], page, app.config['posts_per_page'], 0)

    title = gettext('All Tickets')

    if content and form is not None and hasattr(form, 'content'):
        form.content.data = content

    response = make_response(render_template('flicket_tickets.html',
                                             title=title,
                                             form=form,
                                             tickets=ticket_query,
                                             page=page,
                                             number_results=number_results,
                                             status=status,
                                             department=department,
                                             category=category,
                                             user_id=user_id,
                                             created_id=created_id,
                                             assigned_id=assigned_id,
                                             sort=sort,
                                             base_url='admin_bp.tickets',
                                             show_admin_menu=True))

    if set_cookie:
        response.set_cookie('admin_tickets_sort', sort, max_age=2419200, path=app.config['ADMINHOME'] + 'tickets/')

    return response


def create_user(username, password, email=None, name=None, job_title=None, locale=None, disabled=None):
    password = hash_password(password)
    register = FlicketUser(username=username,
                           email=email,
                           name=name,
                           password=password,
                           job_title=job_title,
                           date_added=datetime.datetime.now(),
                           locale=locale or "",
                           disabled=disabled if disabled is not None else False)
    db.session.add(register)  # type: ignore[attr-defined]
    db.session.commit()  # type: ignore[attr-defined]


# add permissions
@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # set the identity user object
    identity.user = current_user
    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    # Assuming the User model has a list of groups, update the
    # identity with the groups that the user provides
    if hasattr(current_user, 'flicket_groups'):
        the_user = FlicketUser.query.filter_by(id=current_user.id).first()
        for g in the_user.flicket_groups:
            identity.provides.add(RoleNeed('{}'.format(g.group_name)))


@admin_bp.route(app.config['ADMINHOME'])
@login_required
@admin_permission.require(http_exception=403)
def index():
    # noinspection PyUnresolvedReferences
    return render_template('admin.html', title='Admin')


# Admin tickets view - accessible only to admin users
@admin_bp.route(app.config['ADMINHOME'] + 'tickets/', methods=['GET', 'POST'])
@admin_bp.route(app.config['ADMINHOME'] + 'tickets/<int:page>/', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def tickets(page=1):
    response = admin_tickets_view(page)
    return response


# Admin tickets CSV export
@admin_bp.route(app.config['ADMINHOME'] + 'tickets_csv/', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def tickets_csv():
    # get request arguments from the url
    status = request.args.get('status')
    department = request.args.get('department')
    category = request.args.get('category')
    content = request.args.get('content')
    user_id = request.args.get('user_id')

    ticket_query, form = FlicketTicket.query_tickets(department=department, category=category, status=status,
                                                     user_id=user_id, content=content)
    ticket_query = ticket_query.limit(app.config['csv_dump_limit'])

    date_stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    file_name = date_stamp + 'admin_ticketdump.csv'

    csv_contents = 'Ticket_ID,Priority,Title,Submitted By,Date,Replies,Category,Status,Assigned,URL\n'
    for ticket in ticket_query:

        if hasattr(ticket.assigned, 'name'):
            _name = ticket.assigned.name
        else:
            _name = 'Not assigned'

        csv_contents += '{},{},"{}",{},{},{},{} - {},{},{},{}{}\n'.format(ticket.id_zfill,
                                                                          ticket.ticket_priority.priority,
                                                                          clean_csv_data(ticket.title),
                                                                          ticket.user.name,
                                                                          ticket.date_added.strftime("%Y-%m-%d"),
                                                                          ticket.num_replies,
                                                                          clean_csv_data(
                                                                              ticket.category.department.department),
                                                                          clean_csv_data(ticket.category.category),
                                                                          ticket.current_status.status,
                                                                          _name,
                                                                          app.config["base_url"],
                                                                          url_for("flicket_bp.ticket_view",
                                                                                  ticket_id=ticket.id))

    return Response(
        csv_contents,
        mimetype='text/csv',
        headers={"Content-disposition":
                     f"attachment; filename={file_name}"}
    )


# shows all users
@admin_bp.route(app.config['ADMINHOME'] + 'users/', methods=['GET', 'POST'])
@admin_bp.route(app.config['ADMINHOME'] + 'users/<int:page>', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def users(page=1):
    users = FlicketUser.query.order_by(FlicketUser.username)
    users = users.paginate(page=page, per_page=app.config['posts_per_page'])

    # noinspection PyUnresolvedReferences
    return render_template('admin_users.html', title='Users', users=users)  # type: ignore[misc]


# add user
@admin_bp.route(app.config['ADMINHOME'] + 'add_user/', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def add_user():
    form = AddUserForm()
    if form.validate_on_submit():
        create_user(form.username.data,
                    form.password.data,
                    email=form.email.data,
                    name=form.name.data,
                    job_title=form.job_title.data,
                    locale=form.locale.data,
                    disabled=form.disabled.data)
        flash(gettext('You have successfully registered new user "{}".'.format(form.username.data)), category='success')
        return redirect(url_for('admin_bp.users'))
    # noinspection PyUnresolvedReferences
    return render_template('admin_user.html', title='Add User', form=form)


# edit user
@admin_bp.route(app.config['ADMINHOME'] + 'edit_user/', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def edit_user():
    _id = request.args.get('id')
    user = FlicketUser.query.filter_by(id=_id).first()
    if user:
        form = EditUserForm()
        if form.validate_on_submit():
            # check the username is unique
            if user.username != form.username.data:
                query = FlicketUser.query.filter_by(username=form.username.data)
                if query.count() > 0:
                    flash(gettext('Username already exists'), category='warning')
                else:
                    # change the username.
                    user.username = form.username.data
            # Don't change the password if nothing was entered.
            if form.password.data != '':
                user.password = hash_password(form.password.data)

            user.email = form.email.data
            user.name = form.name.data
            user.job_title = form.job_title.data
            user.disabled = form.disabled.data

            groups = form.groups.data
            # bit hacky but until i get better at this.
            # at least it keeps the groups table clean. :/
            # delete all groups associated with current user.
            user.flicket_groups = []  # this is beautifully simple though
            # add the user to selected groups
            for g in groups:
                group_id = FlicketGroup.query.filter_by(id=g).first()
                group_id.users.append(user)
            db.session.commit()  # type: ignore[attr-defined]
            flash(gettext("User {} edited.".format(user.username)), category='success')
            return redirect(url_for('admin_bp.edit_user', id=_id))

        # populate form with form data retrieved from database.
        form.user_id.data = user.id
        form.username.data = user.username
        form.email.data = user.email
        form.name.data = user.name
        form.job_title.data = user.job_title
        form.disabled.data = user.disabled
        # define list of preselect groups.
        groups = []
        for g in user.flicket_groups or []:  # type: ignore[operator]
            groups.append(g.id)
        form.groups.data = groups
    else:
        flash(gettext("Could not find user."), category='warning')
        return redirect(url_for('admin_bp.index'))

    # noinspection PyUnresolvedReferences
    return render_template('admin_user.html',
                           title='Edit User',
                           admin_edit=True,
                           form=form, user=user)  # type: ignore[operator]


# Delete user
@admin_bp.route(app.config['ADMINHOME'] + 'delete_user/', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def delete_user():
    form = EnterPasswordForm()
    id = request.args.get('id')
    user_details = FlicketUser.query.filter_by(id=id).first()

    # we won't ever delete the flicket_admin user (id = 1)
    if id == '1':
        flash(gettext('Can\'t delete default flicket_admin user.'), category='warning')
        return redirect(url_for('admin_bp.index'))

    if form.validate_on_submit():
        # delete the user.
        flash(gettext('Deleted user {}s'.format(user_details.username)), category='success')
        db.session.delete(user_details)  # type: ignore[attr-defined]
        db.session.commit()  # type: ignore[attr-defined]
        return redirect(url_for('admin_bp.users'))
    # populate form with logged in user details
    form.id.data = g.user.id
    # noinspection PyUnresolvedReferences
    return render_template('admin_delete_user.html', title='Delete user',
                           user_details=user_details, form=form)


# Add new groups
@admin_bp.route(app.config['ADMINHOME'] + 'groups/', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def groups():
    form = AddGroupForm()
    groups = FlicketGroup.query.all()
    if form.validate_on_submit():
        add_group = FlicketGroup(
            group_name=form.group_name.data
        )
        db.session.add(add_group)  # type: ignore[attr-defined]
        db.session.commit()  # type: ignore[attr-defined]
        flash(gettext('New group "{}" added.'.format(form.group_name.data)), category='success')
        return redirect(url_for('admin_bp.groups'))

    # noinspection PyUnresolvedReferences
    return render_template('admin_groups.html', title='Groups', form=form, groups=groups)


# Edit groups
@admin_bp.route(app.config['ADMINHOME'] + 'edit_group/', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def admin_edit_group():
    form = AddGroupForm()
    id = request.args.get('id')
    group = FlicketGroup.query.filter_by(id=id).first()

    # if group can't be found in database.
    if not group:
        flash(gettext('Could not find group {}'.format(group.group_name)), category='warning')
        return redirect(url_for('admin_bp.index'))

    # prevent editing of flicket_admin group name as this is hard coded into flicket_admin view permissions.
    if group.group_name == app.config['ADMIN_GROUP_NAME']:
        flash(gettext('Can\'t edit group {}s.'.format(app.config["ADMIN_GROUP_NAME"])), category='warning')
        return redirect(url_for('admin_bp.index'))

    if form.validate_on_submit():
        group.group_name = form.group_name.data
        db.session.commit()  # type: ignore[attr-defined]
        flash(gettext('Group name changed to {}.'.format(group.group_name)), category='success')
        return redirect(url_for('admin_bp.groups'))
    form.group_name.data = group.group_name

    # noinspection PyUnresolvedReferences
    return render_template('admin_edit_group.html', title='Edit Group', form=form)


# Delete group
@admin_bp.route(app.config['ADMINHOME'] + 'delete_group/', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def admin_delete_group():
    form = EnterPasswordForm()
    id = request.args.get('id')
    group_details = FlicketGroup.query.filter_by(id=id).first()

    # we won't ever delete the flicket_admin group (id = 1)
    if id == '1':
        flash(gettext('Can\'t delete default flicket_admin group.'), category='warning')
        return redirect(url_for('admin_bp.index'))

    if form.validate_on_submit():
        # delete the group.
        flash(gettext('Deleted group {}s'.format(group_details.group_name)), category="info")
        db.session.delete(group_details)  # type: ignore[attr-defined]
        db.session.commit()  # type: ignore[attr-defined]
        return redirect(url_for('admin_bp.groups'))
    # populate form with logged in user details
    form.id.data = g.user.id
    title = gettext('Delete Group')
    # noinspection PyUnresolvedReferences
    return render_template('admin_delete_group.html', title=title,
                           group_details=group_details, form=form)


# --- PRIORITIES ---
@admin_bp.route(app.config['ADMINHOME'] + 'priorities/', methods=['GET', 'POST'])
@admin_bp.route(app.config['ADMINHOME'] + 'priorities/<int:page>', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def priorities(page=1):
    query = FlicketPriority.query.order_by(FlicketPriority.priority.asc())
    priorities = query.paginate(page=page, per_page=app.config['posts_per_page'])
    return render_template('admin_priorities/list.html', title='Priorities', priorities=priorities, page=page)

@admin_bp.route(app.config['ADMINHOME'] + 'add_priority/', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def add_priority():
    form = PriorityForm()
    if form.validate_on_submit():
        add_priority = FlicketPriority(priority=form.priority.data)
        db.session.add(add_priority)  # type: ignore[attr-defined]
        db.session.commit()  # type: ignore[attr-defined]
        flash(gettext('New priority "{}" added.'.format(form.priority.data)), category='success')
        return redirect(url_for('admin_bp.priorities'))
    return render_template('admin_priorities/edit.html', title='Add Priority', form=form)

@admin_bp.route(app.config['ADMINHOME'] + 'edit_priority/<int:priority_id>/', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def edit_priority(priority_id):
    priority = FlicketPriority.query.get_or_404(priority_id)
    form = PriorityForm(obj=priority)
    if form.validate_on_submit():
        priority.priority = form.priority.data
        db.session.commit()  # type: ignore[attr-defined]
        flash(gettext('Priority "{}" edited.'.format(form.priority.data)), category='success')
        return redirect(url_for('admin_bp.priorities'))
    form.priority.data = priority.priority
    return render_template('admin_priorities/edit.html', title='Edit Priority', form=form, priority=priority)

@admin_bp.route(app.config['ADMINHOME'] + 'delete_priority/<int:priority_id>/', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def delete_priority(priority_id):
    priority = FlicketPriority.query.get_or_404(priority_id)
    if request.method == 'POST':
        db.session.delete(priority)  # type: ignore[attr-defined]
        db.session.commit()  # type: ignore[attr-defined]
        flash(gettext('Priority "{}" deleted.'.format(priority.priority)), category='success')
        return redirect(url_for('admin_bp.priorities'))
    notification = gettext('You are trying to delete priority: %(value)s.', value=priority.priority.upper())
    return render_template('flicket_delete.html', notification=notification, title='Delete Priority')

# --- STATUS ---
@admin_bp.route(app.config['ADMINHOME'] + 'statuses/', methods=['GET', 'POST'])
@admin_bp.route(app.config['ADMINHOME'] + 'statuses/<int:page>', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def statuses(page=1):
    query = FlicketStatus.query.order_by(FlicketStatus.status.asc())
    statuses = query.paginate(page=page, per_page=app.config['posts_per_page'])
    return render_template('admin_statuses/list.html', title='Statuses', statuses=statuses, page=page)

@admin_bp.route(app.config['ADMINHOME'] + 'add_status/', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def add_status():
    form = StatusForm()
    if form.validate_on_submit():
        add_status = FlicketStatus(status=form.status.data)
        db.session.add(add_status)  # type: ignore[attr-defined]
        db.session.commit()  # type: ignore[attr-defined]
        flash(gettext('New status "{}" added.'.format(form.status.data)), category='success')
        return redirect(url_for('admin_bp.statuses'))
    return render_template('admin_statuses/edit.html', title='Add Status', form=form)

@admin_bp.route(app.config['ADMINHOME'] + 'edit_status/<int:status_id>/', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def edit_status(status_id):
    status = FlicketStatus.query.get_or_404(status_id)
    form = StatusForm(obj=status)
    if form.validate_on_submit():
        status.status = form.status.data
        db.session.commit()  # type: ignore[attr-defined]
        flash(gettext('Status "{}" edited.'.format(form.status.data)), category='success')
        return redirect(url_for('admin_bp.statuses'))
    form.status.data = status.status
    return render_template('admin_statuses/edit.html', title='Edit Status', form=form, status=status)

@admin_bp.route(app.config['ADMINHOME'] + 'delete_status/<int:status_id>/', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def delete_status(status_id):
    status = FlicketStatus.query.get_or_404(status_id)
    if request.method == 'POST':
        db.session.delete(status)  # type: ignore[attr-defined]
        db.session.commit()  # type: ignore[attr-defined]
        flash(gettext('Status "{}" deleted.'.format(status.status)), category='success')
        return redirect(url_for('admin_bp.statuses'))
    notification = gettext('You are trying to delete status: %(value)s.', value=status.status.upper())
    return render_template('flicket_delete.html', notification=notification, title='Delete Status')

# Admin delete ticket
@admin_bp.route(app.config['ADMINHOME'] + 'delete_ticket/<int:ticket_id>/', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def delete_ticket(ticket_id):
    form = ConfirmPassword()
    
    # Use raw SQL to check if ticket exists and get basic info
    try:
        result = db.session.execute("""
            SELECT t.id, t.title, t.content, t.date_added, 
                   u.name as user_name, d.department as dept_name, c.category as cat_name,
                   p.priority as priority_name, s.status as status_name,
                   au.name as assigned_name,
                   (SELECT COUNT(*) FROM flicket_post WHERE ticket_id = t.id) as num_replies,
                   t.hours
            FROM flicket_topic t
            LEFT JOIN flicket_users u ON t.started_id = u.id
            LEFT JOIN flicket_category c ON t.category_id = c.id
            LEFT JOIN flicket_department d ON c.department_id = d.id
            LEFT JOIN flicket_priorities p ON t.ticket_priority_id = p.id
            LEFT JOIN flicket_status s ON t.status_id = s.id
            LEFT JOIN flicket_users au ON t.assigned_id = au.id
            WHERE t.id = :ticket_id
        """, {'ticket_id': ticket_id})
        
        ticket_data = result.fetchone()
        if not ticket_data:
            flash(gettext('Could not find ticket.'), category='warning')
            return redirect(url_for('admin_bp.tickets'))
        
        # Create a MockTicket for display purposes
        ticket = MockTicket(dict(ticket_data))
        
    except Exception as e:
        print(f"Error retrieving ticket for deletion: {e}")
        flash(gettext('Could not find ticket.'), category='warning')
        return redirect(url_for('admin_bp.tickets'))

    if form.validate_on_submit():
        try:
            # Simple deletion - just delete the ticket and related data
            # Delete uploads first
            db.session.execute("DELETE FROM flicket_uploads WHERE topic_id = :ticket_id", {'ticket_id': ticket_id})
            
            # Delete history for posts
            db.session.execute("DELETE FROM flicket_history WHERE post_id IN (SELECT id FROM flicket_post WHERE ticket_id = :ticket_id)", {'ticket_id': ticket_id})
            
            # Delete posts
            db.session.execute("DELETE FROM flicket_post WHERE ticket_id = :ticket_id", {'ticket_id': ticket_id})
            
            # Delete the ticket
            db.session.execute("DELETE FROM flicket_topic WHERE id = :ticket_id", {'ticket_id': ticket_id})
            
            db.session.commit()
            flash(gettext('Ticket deleted.'), category='success')
            return redirect(url_for('admin_bp.tickets'))
            
        except Exception as e:
            print(f"Error deleting ticket: {e}")
            db.session.rollback()
            flash(gettext('Error deleting ticket.'), category='error')
            return redirect(url_for('admin_bp.tickets'))

    return render_template('flicket_deletetopic.html', form=form, ticket=ticket, title='Delete Ticket')
