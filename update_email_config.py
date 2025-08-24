#!/usr/bin/env python3
"""
Script to directly update the database with Gmail email configuration.
This bypasses the web form to ensure the settings are saved correctly.
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from application import app, db
from application.flicket_admin.models.flicket_config import FlicketConfig

def update_email_config():
    """Update the email configuration in the database"""
    
    with app.app_context():
        # Get the current configuration
        config = FlicketConfig.query.first()
        
        if not config:
            print("❌ No configuration found in database!")
            return False
            
        print("📧 Current configuration before update:")
        print(f"   Server: {config.mail_server}")
        print(f"   Port: {config.mail_port}")
        print(f"   TLS: {config.mail_use_tls}")
        print(f"   Username: {config.mail_username}")
        
        # Update with Gmail settings
        config.mail_server = 'smtp.gmail.com'
        config.mail_port = 587
        config.mail_use_tls = True
        config.mail_use_ssl = False
        config.mail_debug = True
        config.mail_username = 'recordablesticketquest@gmail.com'
        config.mail_password = 'ymra bdxk uduu dpna'
        config.mail_default_sender = 'recordablesticketquest@gmail.com'
        config.mail_max_emails = 10
        config.mail_suppress_send = False
        config.mail_ascii_attachments = False
        
        # Commit changes
        db.session.commit()
        
        print("\n✅ Configuration updated!")
        print("📧 New configuration:")
        print(f"   Server: {config.mail_server}")
        print(f"   Port: {config.mail_port}")
        print(f"   TLS: {config.mail_use_tls}")
        print(f"   SSL: {config.mail_use_ssl}")
        print(f"   Debug: {config.mail_debug}")
        print(f"   Username: {config.mail_username}")
        print(f"   Default Sender: {config.mail_default_sender}")
        
        return True

if __name__ == '__main__':
    print("🚀 Updating Email Configuration")
    print("=" * 40)
    
    success = update_email_config()
    
    if success:
        print("\n🎉 Configuration updated successfully!")
        print("Now run: python test_email_config.py")
    else:
        print("\n💥 Failed to update configuration.")
    
    print("\n" + "=" * 40)
