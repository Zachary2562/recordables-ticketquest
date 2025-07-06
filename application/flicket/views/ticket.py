from flask import Blueprint, render_template, redirect, url_for, flash
from application import db
from application.flicket.forms.form_ticket import TicketForm
# from application.flicket.models.flicket_ticket import FlicketTicket

ticket_bp = Blueprint('ticket_bp', __name__)

@ticket_bp.route('/ticket_create/', methods=['GET', 'POST'])
def create_ticket():
    form = TicketForm()
    if form.validate_on_submit():
        category_value = form.category.data
        if category_value == 'other':
            category_value = form.other_category.data

        # Example ticket creation, adjust for your real model
        # ticket = FlicketTicket(
        #     title=form.title.data,
        #     content=form.content.data,
        #     priority=form.priority.data,
        #     category=category_value,
        # )
        # db.session.add(ticket)
        # db.session.commit()

        flash('Ticket created!', 'success')
        return redirect(url_for('ticket_bp.create_ticket'))
    return render_template('flicket/create_ticket.html', form=form)
