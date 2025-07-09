# add_admin.py

from application import app, db
from application.flicket.models.flicket_user import FlicketUser, FlicketGroup
from application.flicket.scripts.hash_password import hash_password
from datetime import datetime

with app.app_context():
    admin_username = "Admin User"
    admin_name = "Admin Name"
    admin_email = "admin@example.com"
    admin_password = "Admin123"
    group_name = getattr(app.config, "ADMIN_GROUP_NAME", "flicket_admin")

    user = FlicketUser.query.filter_by(username=admin_username).first()
    if not user:
        print("Admin user not found. Creating...")
        hashed_pw = hash_password(admin_password)
        user = FlicketUser(
            username=admin_username,
            name=admin_name,
            email=admin_email,
            password=hashed_pw,
            date_added=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        print("Admin user created.")
    else:
        print("Admin user already exists.")

    admin_group = FlicketGroup.query.filter_by(group_name=group_name).first()
    if not admin_group:
        print("Admin group not found. Creating...")
        admin_group = FlicketGroup(group_name=group_name)
        db.session.add(admin_group)
        db.session.commit()
        print(f"Created group: {group_name}")
    if user not in admin_group.users:
        admin_group.users.append(user)
        db.session.commit()
        print("User added to admin group.")
    else:
        print("User already in admin group.")
