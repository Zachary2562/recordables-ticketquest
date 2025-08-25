#! usr/bin/python3
# -*- coding: utf-8 -*-
#
# Flicket - copyright Paul Bourne: evereux@gmail.com

from flask import render_template, g
from flask_login import login_required
from sqlalchemy import and_
from datetime import datetime

from . import flicket_bp
from application import app, db
from application.flicket.scripts.pie_charts import create_pie_chart_dict
from application.flicket.models.flicket_models import FlicketTicket, FlicketStatus, FlicketPriority


# Create a mock ticket class to avoid SQLAlchemy datetime parsing issues
class MockTicket:
    def __init__(self, data):
        self.id = data['id']
        self.title = data['title']
        self.content = data['content']
        
        # Format the date properly
        if data['date_added']:
            try:
                from datetime import datetime
                if isinstance(data['date_added'], str):
                    # Parse the string date and format it
                    dt = datetime.fromisoformat(data['date_added'].replace('Z', '+00:00'))
                    self.date_added = dt.strftime('%Y-%m-%d %I:%M %p') + ' EST'
                else:
                    # It's already a datetime object
                    self.date_added = data['date_added'].strftime('%Y-%m-%d %I:%M %p') + ' EST'
            except:
                # Fallback to original format if parsing fails
                self.date_added = str(data['date_added'])
        else:
            self.date_added = 'No Date'
            
        self.num_replies = data.get('num_replies', 0)
        self.total_hours = data.get('hours', 0)  # Map 'hours' to 'total_hours' for compatibility
        self.id_zfill = str(data['id']).zfill(5)
        
        # Add last_updated attribute for template compatibility
        if data['date_added']:
            try:
                from datetime import datetime
                if isinstance(data['date_added'], str):
                    # Parse the string date and format it
                    dt = datetime.fromisoformat(data['date_added'].replace('Z', '+00:00'))
                    self.last_updated = dt.strftime('%Y-%m-%d')
                else:
                    # It's already a datetime object
                    self.last_updated = data['date_added'].strftime('%Y-%m-%d')
            except:
                # Fallback to original format if parsing fails
                self.last_updated = str(data['date_added'])[:10] if data['date_added'] else 'No Date'
        else:
            self.last_updated = 'No Date'
        
        # Mock relationships
        self.user = MockUser(data.get('user_name', 'Unknown'))
        self.category = MockCategory(data.get('dept_name', 'Unknown'), data.get('cat_name', 'Unknown'))
        self.ticket_priority = MockPriority(data.get('priority_name', 'Unknown'))
        self.current_status = MockStatus(data.get('status_name', 'Unknown'))
        self.assigned = MockUser(data.get('assigned_name', 'Unassigned'))

class MockUser:
    def __init__(self, name):
        self.name = name

class MockCategory:
    def __init__(self, dept_name, cat_name):
        self.department = MockDepartment(dept_name)
        self.category = cat_name

class MockDepartment:
    def __init__(self, name):
        self.department = name

class MockPriority:
    def __init__(self, name):
        self.priority = name

class MockStatus:
    def __init__(self, name):
        self.status = name


# view users
@flicket_bp.route(app.config['FLICKET'], methods=['GET', 'POST'])
@login_required
def index():
    """ View showing flicket main page. We use this to display some statistics."""
    days = 7

    # Get tickets for each priority level using raw SQL to avoid datetime parsing issues
    try:
        # Use raw SQL to get all ticket data
        # For non-admin users, only show their own tickets
        if g.user.is_admin or g.user.is_super_user:
            urgent_result = db.session.execute("""
                SELECT t.id, t.title, t.content, t.date_added, 
                       u.name as user_name, d.department as dept_name, c.category as cat_name,
                       p.priority as priority_name, s.status as status_name,
                       au.name as assigned_name
                FROM flicket_topic t
                LEFT JOIN flicket_users u ON t.started_id = u.id
                LEFT JOIN flicket_category c ON t.category_id = c.id
                LEFT JOIN flicket_department d ON c.department_id = d.id
                LEFT JOIN flicket_priorities p ON t.ticket_priority_id = p.id
                LEFT JOIN flicket_status s ON t.status_id = s.id
                LEFT JOIN flicket_users au ON t.assigned_id = au.id
                WHERE t.ticket_priority_id = 4 AND t.status_id = 1 AND t.date_added IS NOT NULL
                ORDER BY t.id DESC
                LIMIT 100
            """)
        else:
            # For regular users, only show their own tickets
            urgent_result = db.session.execute("""
                SELECT t.id, t.title, t.content, t.date_added, 
                       u.name as user_name, d.department as dept_name, c.category as cat_name,
                       p.priority as priority_name, s.status as status_name,
                       au.name as assigned_name
                FROM flicket_topic t
                LEFT JOIN flicket_users u ON t.started_id = u.id
                LEFT JOIN flicket_category c ON t.category_id = c.id
                LEFT JOIN flicket_department d ON c.department_id = d.id
                LEFT JOIN flicket_priorities p ON t.ticket_priority_id = p.id
                LEFT JOIN flicket_status s ON t.status_id = s.id
                LEFT JOIN flicket_users au ON t.assigned_id = au.id
                WHERE t.ticket_priority_id = 4 AND t.status_id = 1 AND t.date_added IS NOT NULL AND t.started_id = :user_id
                ORDER BY t.id DESC
                LIMIT 100
            """, {'user_id': g.user.id})
        urgent_tickets = [MockTicket(dict(row)) for row in urgent_result]
        
        # For non-admin users, only show their own tickets
        if g.user.is_admin or g.user.is_super_user:
            high_result = db.session.execute("""
                SELECT t.id, t.title, t.content, t.date_added, 
                       u.name as user_name, d.department as dept_name, c.category as cat_name,
                       p.priority as priority_name, s.status as status_name,
                       au.name as assigned_name
                FROM flicket_topic t
                LEFT JOIN flicket_users u ON t.started_id = u.id
                LEFT JOIN flicket_category c ON t.category_id = c.id
                LEFT JOIN flicket_department d ON c.department_id = d.id
                LEFT JOIN flicket_priorities p ON t.ticket_priority_id = p.id
                LEFT JOIN flicket_status s ON t.status_id = s.id
                LEFT JOIN flicket_users au ON t.assigned_id = au.id
                WHERE t.ticket_priority_id = 3 AND t.status_id = 1 AND t.date_added IS NOT NULL
                ORDER BY t.id DESC
                LIMIT 100
            """)
        else:
            # For regular users, only show their own tickets
            high_result = db.session.execute("""
                SELECT t.id, t.title, t.content, t.date_added, 
                       u.name as user_name, d.department as dept_name, c.category as cat_name,
                       p.priority as priority_name, s.status as status_name,
                       au.name as assigned_name
                FROM flicket_topic t
                LEFT JOIN flicket_users u ON t.started_id = u.id
                LEFT JOIN flicket_category c ON t.category_id = c.id
                LEFT JOIN flicket_department d ON c.department_id = d.id
                LEFT JOIN flicket_priorities p ON t.ticket_priority_id = p.id
                LEFT JOIN flicket_status s ON t.status_id = s.id
                LEFT JOIN flicket_users au ON t.assigned_id = au.id
                WHERE t.ticket_priority_id = 3 AND t.status_id = 1 AND t.date_added IS NOT NULL AND t.started_id = :user_id
                ORDER BY t.id DESC
                LIMIT 100
            """, {'user_id': g.user.id})
        high_tickets = [MockTicket(dict(row)) for row in high_result]
        
        # For non-admin users, only show their own tickets
        if g.user.is_admin or g.user.is_super_user:
            medium_result = db.session.execute("""
                SELECT t.id, t.title, t.content, t.date_added, 
                       u.name as user_name, d.department as dept_name, c.category as cat_name,
                       p.priority as priority_name, s.status as status_name,
                       au.name as assigned_name
                FROM flicket_topic t
                LEFT JOIN flicket_users u ON t.started_id = u.id
                LEFT JOIN flicket_category c ON t.category_id = c.id
                LEFT JOIN flicket_department d ON c.department_id = d.id
                LEFT JOIN flicket_priorities p ON t.ticket_priority_id = p.id
                LEFT JOIN flicket_status s ON t.status_id = s.id
                LEFT JOIN flicket_users au ON t.assigned_id = au.id
                WHERE t.ticket_priority_id = 2 AND t.status_id = 1 AND t.date_added IS NOT NULL
                ORDER BY t.id DESC
                LIMIT 100
            """)
        else:
            # For regular users, only show their own tickets
            medium_result = db.session.execute("""
                SELECT t.id, t.title, t.content, t.date_added, 
                       u.name as user_name, d.department as dept_name, c.category as cat_name,
                       p.priority as priority_name, s.status as status_name,
                       au.name as assigned_name
                FROM flicket_topic t
                LEFT JOIN flicket_users u ON t.started_id = u.id
                LEFT JOIN flicket_category c ON t.category_id = c.id
                LEFT JOIN flicket_department d ON c.department_id = d.id
                LEFT JOIN flicket_priorities p ON t.ticket_priority_id = p.id
                LEFT JOIN flicket_status s ON t.status_id = s.id
                LEFT JOIN flicket_users au ON t.assigned_id = au.id
                WHERE t.ticket_priority_id = 2 AND t.status_id = 1 AND t.date_added IS NOT NULL AND t.started_id = :user_id
                ORDER BY t.id DESC
                LIMIT 100
            """, {'user_id': g.user.id})
        medium_tickets = [MockTicket(dict(row)) for row in medium_result]
        
        # For non-admin users, only show their own tickets
        if g.user.is_admin or g.user.is_super_user:
            low_result = db.session.execute("""
                SELECT t.id, t.title, t.content, t.date_added, 
                       u.name as user_name, d.department as dept_name, c.category as cat_name,
                       p.priority as priority_name, s.status as status_name,
                       au.name as assigned_name
                FROM flicket_topic t
                LEFT JOIN flicket_users u ON t.started_id = u.id
                LEFT JOIN flicket_category c ON t.category_id = c.id
                LEFT JOIN flicket_department d ON c.department_id = d.id
                LEFT JOIN flicket_priorities p ON t.ticket_priority_id = p.id
                LEFT JOIN flicket_status s ON t.status_id = s.id
                LEFT JOIN flicket_users au ON t.assigned_id = au.id
                WHERE t.ticket_priority_id = 1 AND t.status_id = 1 AND t.date_added IS NOT NULL
                ORDER BY t.id DESC
                LIMIT 100
            """)
        else:
            # For regular users, only show their own tickets
            low_result = db.session.execute("""
                SELECT t.id, t.title, t.content, t.date_added, 
                       u.name as user_name, d.department as dept_name, c.category as cat_name,
                       p.priority as priority_name, s.status as status_name,
                       au.name as assigned_name
                FROM flicket_topic t
                LEFT JOIN flicket_users u ON t.started_id = u.id
                LEFT JOIN flicket_category c ON t.category_id = c.id
                LEFT JOIN flicket_department d ON c.department_id = d.id
                LEFT JOIN flicket_priorities p ON t.ticket_priority_id = p.id
                LEFT JOIN flicket_status s ON t.status_id = s.id
                LEFT JOIN flicket_users au ON t.assigned_id = au.id
                WHERE t.ticket_priority_id = 1 AND t.status_id = 1 AND t.date_added IS NOT NULL AND t.started_id = :user_id
                ORDER BY t.id DESC
                LIMIT 100
            """, {'user_id': g.user.id})
        low_tickets = [MockTicket(dict(row)) for row in low_result]
        
    except Exception as e:
        # If there's an error with the query, return empty results
        print(f"Error querying tickets: {e}")
        urgent_tickets = []
        high_tickets = []
        medium_tickets = []
        low_tickets = []

    # PIE CHARTS
    ids, graph_json = create_pie_chart_dict()

    # Calculate open ticket count for admin dashboard
    open_count = 0
    if g.user.is_admin or g.user.is_super_user:
        try:
            result = db.session.execute("SELECT COUNT(*) FROM flicket_topic WHERE status_id = 1")
            open_count = result.fetchone()[0]
        except Exception as e:
            print(f"Error calculating open count: {e}")
            open_count = 0

    return render_template('flicket_index.html',
                           days=days,
                           urgent_tickets=urgent_tickets,
                           high_tickets=high_tickets,
                           medium_tickets=medium_tickets,
                           low_tickets=low_tickets,
                           ids=ids,
                           graph_json=graph_json,
                           open_count=open_count)
