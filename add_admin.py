# add_admin.py

from application import app, db
from application.flicket.models.flicket_user import FlicketUser, FlicketGroup

with app.app_context():
    # Change "admin" to your actual username if needed
    user = FlicketUser.query.filter_by(username="admin").first()
    if not user:
        print("Admin user not found.")
        exit(1)
    group_name = getattr(app.config, "ADMIN_GROUP_NAME", "flicket_admin")
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
