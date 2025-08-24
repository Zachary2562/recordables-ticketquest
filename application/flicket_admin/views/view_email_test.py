#! usr/bin/python3
# -*- coding: utf8 -*-
#
# Flicket - copyright Paul Bourne: evereux@gmail.com

from flask import flash
from flask import Markup
from flask import url_for
from flask import render_template
from flask_babel import gettext
from flask_login import login_required

from application import app
from application.flicket_admin.forms.form_config import EmailTest
from application.flicket.scripts.email import FlicketMail

from . import admin_bp
from .view_admin import admin_permission


# Configuration view
@admin_bp.route(app.config['ADMINHOME'] + 'test_email/', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def email_test():
    form = EmailTest()

    if form.validate_on_submit():
        # send email notification
        try:
            mail = FlicketMail()
            mail.test_email([form.email_address.data])
            config_href = app.config.get("base_url", "") + url_for('admin_bp.config')
            msg = gettext(
                'Flicket has tried to send an email to the address you entered. Please check your inbox. If no email has '
                'arrived please double check the <a href="{href}">config</a> settings.'
            )
            flash(Markup(msg.format(href=config_href)), category='success')
        except Exception as e:
            config_href = app.config.get("base_url", "") + url_for('admin_bp.config')
            msg = gettext(
                'Failed to send test email. Error: {error}. Please check the <a href="{href}">config</a> settings.'
            )
            flash(Markup(msg.format(error=str(e), href=config_href)), category='error')

    return render_template('admin_email_test.html',
                           title='Send Email Test',
                           form=form)
