import sys
import os

# Ensure the grandparent directory (project root) is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from application import db
from application.flicket.models.flicket_config import FlicketConfig

config = FlicketConfig(
    mail_server='localhost',
    mail_port=25,
    mail_use_tls=False,
    mail_use_ssl=False,
    mail_debug=False,
    mail_username='',
    mail_password='',
    mail_default_sender='',
    mail_max_emails=0,
    mail_suppress_send=False,
    mail_ascii_attachments=False,
    posts_per_page=10,
    allowed_extensions='txt,jpg,png,pdf',
    ticket_upload_folder='uploads/tickets',
    avatar_upload_folder='uploads/avatars',
    application_title='Flicket',
    base_url='http://127.0.0.1:5000/',
    auth_domain='',
    use_auth_domain=False,
    csv_dump_limit=1000,
    change_category=False,
    change_category_only_admin_or_super_user=False
)

db.session.add(config)
db.session.commit()

print("Flicket config inserted successfully!")
