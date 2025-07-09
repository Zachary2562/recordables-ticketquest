from flask import Blueprint, render_template, redirect, url_for, flash, request
from application.flicket.forms.form_signup import SignUpForm
from application.flicket.models.flicket_user import FlicketUser
from application.flicket.scripts.hash_password import hash_password
from datetime import datetime

signup_bp = Blueprint('signup_bp', __name__)

@signup_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    from application import db  # moved inside function to avoid circular import
    form = SignUpForm()
    if form.validate_on_submit():
        # Prevent creation of admin user from signup
        if form.username.data.lower() in ['admin', 'admin user']:
            flash('You cannot create an admin account from signup.', 'danger')
            return render_template('flicket/signup.html', form=form)
        # Hash the password
        hashed_pw = hash_password(form.password.data)
        # Create user
        user = FlicketUser(
            username=form.username.data,
            name=form.name.data,
            email=form.email.data,
            password=hashed_pw,
            date_added=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('flicket_bp.login'))
    return render_template('flicket/signup.html', form=form) 