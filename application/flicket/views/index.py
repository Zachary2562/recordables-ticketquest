#! usr/bin/python3
# -*- coding: utf-8 -*-
#
# Flicket - copyright Paul Bourne: evereux@gmail.com

from flask import render_template, g
from flask_login import login_required
from sqlalchemy import and_

from . import flicket_bp
from application import app
from application.flicket.scripts.pie_charts import create_pie_chart_dict
from application.flicket.models.flicket_models import FlicketTicket, FlicketStatus, FlicketPriority


# view users
@flicket_bp.route(app.config['FLICKET'], methods=['GET', 'POST'])
@login_required
def index():
    """ View showing flicket main page. We use this to display some statistics."""
    days = 7

    # Get tickets for each priority level in ranked order (Urgent, High, Medium, Low)
    # Filter out tickets with problematic date values
    try:
        urgent_tickets = FlicketTicket.query.filter(
            and_(
                FlicketTicket.ticket_priority_id == 4,
                FlicketTicket.status_id == 1,
                FlicketTicket.date_added.isnot(None)
            )
        ).limit(100)
        
        high_tickets = FlicketTicket.query.filter(
            and_(
                FlicketTicket.ticket_priority_id == 3,
                FlicketTicket.status_id == 1,
                FlicketTicket.date_added.isnot(None)
            )
        ).limit(100)
        
        medium_tickets = FlicketTicket.query.filter(
            and_(
                FlicketTicket.ticket_priority_id == 2,
                FlicketTicket.status_id == 1,
                FlicketTicket.date_added.isnot(None)
            )
        ).limit(100)
        
        low_tickets = FlicketTicket.query.filter(
            and_(
                FlicketTicket.ticket_priority_id == 1,
                FlicketTicket.status_id == 1,
                FlicketTicket.date_added.isnot(None)
            )
        ).limit(100)
    except Exception as e:
        # If there's an error with the query, return empty results
        print(f"Error querying tickets: {e}")
        urgent_tickets = FlicketTicket.query.filter_by(id=0)  # Empty query
        high_tickets = FlicketTicket.query.filter_by(id=0)    # Empty query
        medium_tickets = FlicketTicket.query.filter_by(id=0)  # Empty query
        low_tickets = FlicketTicket.query.filter_by(id=0)     # Empty query

    # PIE CHARTS
    ids, graph_json = create_pie_chart_dict()

    # Calculate open ticket count for admin dashboard
    open_count = 0
    if g.user.is_admin or g.user.is_super_user:
        try:
            open_status = FlicketStatus.query.filter_by(status='Open').first()
            if open_status:
                open_count = FlicketTicket.query.filter_by(status_id=open_status.id).count()
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
