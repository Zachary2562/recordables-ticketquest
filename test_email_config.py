#!/usr/bin/env python3
"""
Test script to verify email configuration is working correctly.
Run this script to test if your Gmail SMTP settings are properly configured.
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from application import app, db
from application.flicket_admin.models.flicket_config import FlicketConfig
from flask_mail import Mail, Message

def test_email_config():
    """Test the current email configuration"""
    
    with app.app_context():
        # Get the current configuration from database
        config = FlicketConfig.query.first()
        
        if not config:
            print("❌ No configuration found in database!")
            return False
            
        print("📧 Current Email Configuration:")
        print(f"   Server: {config.mail_server}")
        print(f"   Port: {config.mail_port}")
        print(f"   TLS: {config.mail_use_tls}")
        print(f"   SSL: {config.mail_use_ssl}")
        print(f"   Username: {config.mail_username}")
        print(f"   Default Sender: {config.mail_default_sender}")
        print(f"   Debug: {config.mail_debug}")
        
        # Check if Gmail settings are configured
        if config.mail_server != 'smtp.gmail.com':
            print("⚠️  Warning: Server is not set to smtp.gmail.com")
            
        if config.mail_port != 587:
            print("⚠️  Warning: Port is not set to 587 (Gmail TLS)")
            
        if not config.mail_use_tls:
            print("⚠️  Warning: TLS is not enabled (required for Gmail)")
            
        if config.mail_use_ssl:
            print("⚠️  Warning: SSL is enabled (should be disabled for Gmail TLS)")
            
        if not config.mail_username or '@gmail.com' not in config.mail_username:
            print("⚠️  Warning: Username doesn't appear to be a Gmail address")
            
        if not config.mail_password:
            print("❌ Error: No password configured!")
            return False
            
        # Update Flask app config with database settings
        app.config.update(
            MAIL_SERVER=config.mail_server,
            MAIL_PORT=config.mail_port,
            MAIL_USE_TLS=config.mail_use_tls,
            MAIL_USE_SSL=config.mail_use_ssl,
            MAIL_DEBUG=config.mail_debug,
            MAIL_USERNAME=config.mail_username,
            MAIL_PASSWORD=config.mail_password,
            MAIL_DEFAULT_SENDER=config.mail_default_sender,
        )
        
        # Initialize mail
        mail = Mail(app)
        
        # Test sending an email
        try:
            print("\n🧪 Testing email configuration...")
            
            # Create a test message
            msg = Message(
                'Flicket Email Configuration Test',
                sender=config.mail_default_sender,
                recipients=[config.mail_username],  # Send to self for testing
                body='This is a test email to verify your Flicket email configuration is working correctly.'
            )
            
            # Send the email
            mail.send(msg)
            print("✅ Email sent successfully!")
            print("📬 Check your inbox for the test email.")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            print("\n🔧 Troubleshooting tips:")
            print("1. Make sure you're using a Gmail App Password (not your regular password)")
            print("2. Verify the server is 'smtp.gmail.com' and port is 587")
            print("3. Ensure TLS is enabled and SSL is disabled")
            print("4. Check that 2-factor authentication is enabled on your Gmail account")
            print("5. Generate a new App Password if needed")
            return False

if __name__ == '__main__':
    print("🚀 Flicket Email Configuration Test")
    print("=" * 40)
    
    success = test_email_config()
    
    if success:
        print("\n🎉 Email configuration is working correctly!")
    else:
        print("\n💥 Email configuration needs to be fixed.")
        print("Please check the admin configuration at /flicket_admin/config/")
    
    print("\n" + "=" * 40)
