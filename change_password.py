#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Change admin password script for Flicket
"""

from application import app, db
from application.flicket.models.flicket_user import FlicketUser
from application.flicket.scripts.hash_password import hash_password

def change_admin_password(new_password):
    """Change the admin user's password"""
    with app.app_context():
        # Find the admin user
        user = FlicketUser.query.filter_by(username="admin").first()
        if not user:
            print("Admin user not found!")
            return False
        
        # Hash the new password
        hashed_password = hash_password(new_password)
        
        # Update the password
        user.password = hashed_password
        db.session.commit()  # type: ignore[attr-defined]
        
        print(f"Password changed successfully for user 'admin'")
        print(f"New password: {new_password}")
        return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python change_password.py <new_password>")
        print("Example: python change_password.py Admin123")
        sys.exit(1)
    
    new_password = sys.argv[1]
    change_admin_password(new_password) 