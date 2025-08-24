#!/usr/bin/env python3
"""
Debug script to test form submission and validation.
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from application import app
from application.flicket_admin.forms.form_config import ConfigForm

def test_form():
    """Test form creation and validation"""
    
    with app.app_context():
        print("🧪 Testing Form Configuration")
        print("=" * 40)
        
        # Create a form
        form = ConfigForm()
        
        print("📝 Form fields:")
        for field_name, field in form._fields.items():
            if field_name != 'csrf_token':
                print(f"   {field_name}: {type(field).__name__}")
        
        print("\n🔍 Form validation test:")
        
        # Test with valid data
        test_data = {
            'mail_server': 'smtp.gmail.com',
            'mail_port': 587,
            'mail_use_tls': True,
            'mail_use_ssl': False,
            'mail_debug': True,
            'mail_username': 'recordablesticketquest@gmail.com',
            'mail_password': 'ymra bdxk uduu dpna',
            'mail_default_sender': 'recordablesticketquest@gmail.com',
            'mail_max_emails': 10,
            'mail_suppress_send': False,
            'mail_ascii_attachments': False,
            'application_title': 'Flicket',
            'posts_per_page': 50,
            'allowed_extensions': 'txt,jpg,png,pdf',
            'ticket_upload_folder': 'uploads/tickets',
            'base_url': 'http://127.0.0.1:8000/',
            'use_auth_domain': False,
            'auth_domain': '',
            'csv_dump_limit': 1000,
            'change_category': False,
            'change_category_only_admin_or_super_user': False,
            'submit': 'Submit'
        }
        
        # Create form with data
        form = ConfigForm(data=test_data)
        
        print(f"Form valid: {form.validate()}")
        if not form.validate():
            print("Form errors:")
            for field, errors in form.errors.items():
                print(f"   {field}: {errors}")
        else:
            print("✅ Form validation passed!")
            
            # Test accessing form data
            print("\n📊 Form data:")
            print(f"   mail_server: {form.mail_server.data}")
            print(f"   mail_port: {form.mail_port.data}")
            print(f"   mail_use_tls: {form.mail_use_tls.data}")
            print(f"   mail_username: {form.mail_username.data}")

if __name__ == '__main__':
    test_form()
