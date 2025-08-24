#! usr/bin/python3
# -*- coding: utf8 -*-
#
# Flicket - copyright Paul Bourne: evereux@gmail.com

from flask import (flash,
                   redirect,
                   render_template,
                   url_for,
                   request)
from flask_babel import gettext
from flask_login import login_required

from application import app, db, mail
from application.flicket_admin.forms.form_config import ConfigForm
from application.flicket_admin.models.flicket_config import FlicketConfig

from . import admin_bp
from .view_admin import admin_permission


# Configuration view
@admin_bp.route(app.config['ADMINHOME'] + 'config/', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def config():
    form = ConfigForm()

    config_details = FlicketConfig.query.first()
    
    # Ensure we have a config record
    if not config_details:
        # Create default config if none exists
        config_details = FlicketConfig(
            mail_server='localhost',
            mail_port=25,
            mail_use_tls=False,
            mail_use_ssl=False,
            mail_debug=False,
            mail_username='',
            mail_password='',
            mail_default_sender='',
            mail_max_emails=10,
            mail_suppress_send=False,
            mail_ascii_attachments=False,
            posts_per_page=50,
            allowed_extensions='txt,jpg,png,pdf',
            ticket_upload_folder='uploads/tickets',
            avatar_upload_folder='uploads/avatars',
            application_title='Flicket',
            base_url='http://127.0.0.1:8000/',
            auth_domain='',
            use_auth_domain=False,
            csv_dump_limit=1000,
            change_category=False,
            change_category_only_admin_or_super_user=False
        )
        db.session.add(config_details)
        db.session.commit()

    # Debug: Check if form is being submitted
    if request.method == 'POST':
        print(f"Form submitted. Valid: {form.validate()}")
        if not form.validate():
            print(f"Form errors: {form.errors}")
    
    if form.validate_on_submit():

        # Update database with form data - add proper validation and trimming
        if form.mail_server.data:
            config_details.mail_server = form.mail_server.data.strip()
        if form.mail_port.data:
            config_details.mail_port = int(form.mail_port.data)
        config_details.mail_use_tls = form.mail_use_tls.data or False
        config_details.mail_use_ssl = form.mail_use_ssl.data or False
        config_details.mail_debug = form.mail_debug.data or False
        if form.mail_username.data:
            config_details.mail_username = form.mail_username.data.strip()

        if form.mail_default_sender.data:
            config_details.mail_default_sender = form.mail_default_sender.data.strip()
        if form.mail_max_emails.data:
            config_details.mail_max_emails = int(form.mail_max_emails.data)
        config_details.mail_suppress_send = form.mail_suppress_send.data or False
        config_details.mail_ascii_attachments = form.mail_ascii_attachments.data or False

        config_details.application_title = form.application_title.data
        config_details.posts_per_page = form.posts_per_page.data
        config_details.allowed_extensions = form.allowed_extensions.data
        config_details.ticket_upload_folder = form.ticket_upload_folder.data
        config_details.base_url = form.base_url.data

        config_details.use_auth_domain = form.use_auth_domain.data
        config_details.auth_domain = form.auth_domain.data or False

        config_details.csv_dump_limit = form.csv_dump_limit.data

        config_details.change_category = form.change_category.data or False
        config_details.change_category_only_admin_or_super_user = form.change_category_only_admin_or_super_user.data

        # Don't change the password if nothing was entered.
        if form.mail_password.data != '':
            config_details.mail_password = form.mail_password.data
            
        # Commit changes to database
        db.session.commit()
        
        # Debug: Print saved values
        print(f"Saved mail_server: {config_details.mail_server}")
        print(f"Saved mail_port: {config_details.mail_port}")
        print(f"Saved mail_use_tls: {config_details.mail_use_tls}")
        print(f"Saved mail_username: {config_details.mail_username}")
        
        # Update Flask app configuration with new mail settings
        app.config.update(
            MAIL_SERVER=config_details.mail_server,
            MAIL_PORT=config_details.mail_port,
            MAIL_USE_TLS=config_details.mail_use_tls,
            MAIL_USE_SSL=config_details.mail_use_ssl,
            MAIL_DEBUG=config_details.mail_debug,
            MAIL_USERNAME=config_details.mail_username,
            MAIL_PASSWORD=config_details.mail_password,
            MAIL_DEFAULT_SENDER=config_details.mail_default_sender,
            MAIL_MAX_EMAILS=config_details.mail_max_emails,
            MAIL_SUPPRESS_SEND=config_details.mail_suppress_send,
            MAIL_ASCII_ATTACHMENTS=config_details.mail_ascii_attachments,
        )
        
        # Reinitialize mail with new configuration
        mail.init_app(app)
        
        # Debug: Print current app config
        print(f"App config MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
        print(f"App config MAIL_PORT: {app.config.get('MAIL_PORT')}")
        print(f"App config MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
        print(f"App config MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
        
        flash(gettext('Config details updated.'), category='success')
        return redirect(url_for('admin_bp.config'))

    # Debug: Print loaded values from database
    print(f"Loaded mail_server: {config_details.mail_server}")
    print(f"Loaded mail_port: {config_details.mail_port}")
    print(f"Loaded mail_use_tls: {config_details.mail_use_tls}")
    print(f"Loaded mail_username: {config_details.mail_username}")
    
    # populate form with details from database.
    form.mail_server.data = config_details.mail_server
    form.mail_port.data = config_details.mail_port
    form.mail_use_tls.data = config_details.mail_use_tls
    form.mail_use_ssl.data = config_details.mail_use_ssl
    form.mail_debug.data = config_details.mail_debug
    form.mail_username.data = config_details.mail_username
    form.mail_password.data = config_details.mail_password
    form.mail_default_sender.data = config_details.mail_default_sender
    form.mail_max_emails.data = config_details.mail_max_emails
    form.mail_suppress_send.data = config_details.mail_suppress_send
    form.mail_ascii_attachments.data = config_details.mail_ascii_attachments

    form.application_title.data = config_details.application_title

    form.posts_per_page.data = config_details.posts_per_page
    form.allowed_extensions.data = config_details.allowed_extensions
    form.ticket_upload_folder.data = config_details.ticket_upload_folder
    form.base_url.data = config_details.base_url

    form.use_auth_domain.data = config_details.use_auth_domain
    form.auth_domain.data = config_details.auth_domain

    form.csv_dump_limit.data = config_details.csv_dump_limit

    form.change_category.data = config_details.change_category
    form.change_category_only_admin_or_super_user.data = config_details.change_category_only_admin_or_super_user

    return render_template('admin_config.html',
                           title='Flicket Configuration',
                           form=form)
