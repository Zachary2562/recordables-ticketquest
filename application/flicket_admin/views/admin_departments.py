#! usr/bin/python3
# -*- coding: utf8 -*-
#
# Flicket - copyright Paul Bourne: evereux@gmail.com

from flask import flash, redirect, url_for, render_template, g, request
from flask_babel import gettext
from flask_login import login_required

from application import app, db
from application.flicket.models.flicket_models import FlicketDepartment
from application.flicket.forms.flicket_forms import DepartmentForm
from application.flicket_admin.forms.forms_admin import EnterPasswordForm
from . import admin_bp


# list departments
@admin_bp.route(app.config['ADMINHOME'] + 'departments/', methods=['GET', 'POST'])
@admin_bp.route(app.config['ADMINHOME'] + 'departments/<int:page>', methods=['GET', 'POST'])
@login_required
def departments(page=1):
    if not g.user.is_admin:
        flash(gettext('You are not authorised to access this page.'), category='warning')
        return redirect(url_for('admin_bp.index'))

    query = FlicketDepartment.query.order_by(FlicketDepartment.department.asc())
    departments = query.paginate(page=page, per_page=app.config['posts_per_page'])

    return render_template('admin_departments/list.html',
                           title='Departments',
                           departments=departments,
                           page=page)


# add department
@admin_bp.route(app.config['ADMINHOME'] + 'add_department/', methods=['GET', 'POST'])
@login_required
def add_department():
    if not g.user.is_admin:
        flash(gettext('You are not authorised to access this page.'), category='warning')
        return redirect(url_for('admin_bp.index'))

    form = DepartmentForm()
    if form.validate_on_submit():
        add_department = FlicketDepartment(department=form.department.data)
        db.session.add(add_department)
        db.session.commit()
        flash(gettext('New department "{}" added.'.format(form.department.data)), category='success')
        return redirect(url_for('admin_bp.departments'))

    return render_template('admin_departments/edit.html',
                           title='Add Department',
                           form=form)


# edit department
@admin_bp.route(app.config['ADMINHOME'] + 'edit_department/<int:department_id>/', methods=['GET', 'POST'])
@login_required
def edit_department(department_id):
    if not g.user.is_admin:
        flash(gettext('You are not authorised to access this page.'), category='warning')
        return redirect(url_for('admin_bp.index'))

    department = FlicketDepartment.query.get_or_404(department_id)
    form = DepartmentForm()

    if form.validate_on_submit():
        department.department = form.department.data
        db.session.commit()
        flash(gettext('Department "%(value)s" edited.', value=form.department.data), category='success')
        return redirect(url_for('admin_bp.departments'))

    form.department.data = department.department

    return render_template('admin_departments/edit.html',
                           title='Edit Department',
                           form=form,
                           department=department)


# delete department
@admin_bp.route(app.config['ADMINHOME'] + 'delete_department/<int:department_id>/', methods=['GET', 'POST'])
@login_required
def delete_department(department_id):
    if not g.user.is_admin:
        flash(gettext('You are not authorised to access this page.'), category='warning')
        return redirect(url_for('admin_bp.index'))

    department = FlicketDepartment.query.get_or_404(department_id)
    form = EnterPasswordForm()

    # Check if department has categories linked to it
    if len(department.categories) > 0:
        flash(gettext(
            ('Department has categories linked to it. Department can not be deleted unless all categories are '
             'first removed.')),
            category="danger")
        return redirect(url_for('admin_bp.departments'))

    if form.validate_on_submit():
        db.session.delete(department)
        db.session.commit()
        flash(gettext('Department "{}" deleted.'.format(department.department)), category='success')
        return redirect(url_for('admin_bp.departments'))

    notification = gettext(
        "You are trying to delete department: %(value)s.",
        value=department.department.upper())

    return render_template('flicket_delete.html',
                           form=form,
                           notification=notification,
                           title='Delete Department') 