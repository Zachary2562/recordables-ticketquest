#! usr/bin/python3
# -*- coding: utf-8 -*-
#
# Flicket - copyright Paul Bourne: evereux@gmail.com

from datetime import datetime

from flask import g
from flask import redirect
from flask import request
from flask import make_response
from flask import render_template
from flask import Response
from flask import url_for
from flask import flash
from flask_babel import gettext
from flask_login import login_required

from application import app, db
from application.flicket.forms.search import SearchTicketForm
from application.flicket.models.flicket_models import FlicketTicket, FlicketStatus
from . import flicket_bp

# Import the Mock classes from index.py
from .index import MockTicket, MockUser, MockCategory, MockDepartment, MockPriority, MockStatus


def clean_csv_data(input_text):
    output_text = input_text.replace('"', "'")

    return output_text


def tickets_view(page, is_my_view=False, subscribed=False):
    """
        Function common to 'tickets' and 'my_tickets' expect where query is filtered for users own tickets.
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
        redirect_url = FlicketTicket.form_redirect(form, url='flicket_bp.tickets')

        return redirect(redirect_url)

    arg_sort = request.args.get('sort')
    if arg_sort:
        args = request.args.copy()
        del args['sort']
        # Filter out keys that might cause type issues with url_for
        filtered_args = {k: v for k, v in args.items() if k not in ['_external', '_scheme', '_anchor']}

        response = make_response(redirect(url_for('flicket_bp.tickets', **filtered_args)))  # type: ignore[arg-type]
        response.set_cookie('tickets_sort', arg_sort, max_age=2419200, path=url_for('flicket_bp.tickets', **filtered_args))  # type: ignore[arg-type]

        return response

    sort = request.cookies.get('tickets_sort')
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
            
        # Filter for user's own tickets if needed
        if is_my_view and not g.user.is_admin:
            sql_query += f" AND t.started_id = {g.user.id}"
            
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
        print(f"Error querying tickets: {e}")
        # Fallback to empty results
        number_results = 0
        ticket_query = SimplePagination([], page, app.config['posts_per_page'], 0)

    title = gettext('Tickets')
    if subscribed:
        title = gettext('Subscribed Tickets')
    elif is_my_view:
        if assigned_id:
            title = gettext('Assigned Tickets')
        else:
            if g.user.is_admin:
                title = gettext('All Tickets')
            else:
                title = gettext('My Tickets')

    if content and hasattr(form, 'content') and form is not None:
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
                                             base_url='flicket_bp.tickets'))

    if set_cookie:
        response.set_cookie('tickets_sort', sort, max_age=2419200, path=url_for('flicket_bp.tickets'))  # type: ignore[arg-type]

    return response


# tickets main
@flicket_bp.route(app.config['FLICKET'] + 'tickets/', methods=['GET', 'POST'])
@flicket_bp.route(app.config['FLICKET'] + 'tickets/<int:page>/', methods=['GET', 'POST'])
@login_required
def tickets(page=1):
    # Only allow admin users to access the tickets view
    if not (g.user.is_admin or g.user.is_super_user):
        flash(gettext('Access denied. Only administrators can view all tickets.'), category='warning')
        return redirect(url_for('flicket_bp.index'))
    
    # Redirect admin users to admin tickets view
    args = {k: v for k, v in request.args.items() if k not in ['_external', '_scheme', '_anchor']}
    return redirect(url_for('admin_bp.tickets', page=page, **args))  # type: ignore[arg-type]


@flicket_bp.route(app.config['FLICKET'] + 'tickets_csv/', methods=['GET', 'POST'])
@login_required
def tickets_csv():
    # Only allow admin users to access the tickets CSV export
    if not (g.user.is_admin or g.user.is_super_user):
        flash(gettext('Access denied. Only administrators can export tickets.'), category='warning')
        return redirect(url_for('flicket_bp.index'))
    
    # Redirect admin users to admin CSV export
    args = {k: v for k, v in request.args.items() if k not in ['_external', '_scheme', '_anchor']}
    return redirect(url_for('admin_bp.tickets_csv', **args))  # type: ignore[arg-type]


@flicket_bp.route(app.config['FLICKET'] + 'my_tickets/', methods=['GET', 'POST'])
@flicket_bp.route(app.config['FLICKET'] + 'my_tickets/<int:page>/', methods=['GET', 'POST'])
@login_required
def my_tickets(page=1):
    response = tickets_view(page, is_my_view=True)

    return response


@flicket_bp.route(app.config['FLICKET'] + 'subscribed/', methods=['GET', 'POST'])
@flicket_bp.route(app.config['FLICKET'] + 'subscribed/<int:page>/', methods=['GET', 'POST'])
@login_required
def subscribed(page=1):
    response = tickets_view(page, subscribed=True)

    return response
