#! usr/bin/python3
# -*- coding: utf-8 -*-
#
# Flicket - copyright Paul Bourne: evereux@gmail.com

from flask import render_template, g
from flask_login import login_required

from . import flicket_bp
from application import app
from application.flicket.scripts.pie_charts import create_pie_chart_dict
from application.flicket.models.flicket_models import FlicketTicket, FlicketStatus


# view users
@flicket_bp.route(app.config['FLICKET'], methods=['GET', 'POST'])
@login_required
def index():
    """ View showing flicket main page. We use this to display some statistics."""
    days = 7

    # CAROUSEL
    tickets = FlicketTicket.carousel_query()

    # PIE CHARTS
    ids, graph_json = create_pie_chart_dict()

    # Calculate open ticket count for admin dashboard
    open_count = 0
    if g.user.is_admin or g.user.is_super_user:
        open_status = FlicketStatus.query.filter_by(status='Open').first()
        if open_status:
            open_count = FlicketTicket.query.filter_by(status_id=open_status.id).count()

    return render_template('flicket_index.html',
                           days=days,
                           tickets=tickets,
                           ids=ids,
                           graph_json=graph_json,
                           open_count=open_count)
