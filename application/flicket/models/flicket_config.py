from application import db

class FlicketConfig(db.Model):
    __tablename__ = 'flicket_config'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    mail_server = db.Column(db.String(128))
    mail_port = db.Column(db.Integer)
    mail_use_tls = db.Column(db.Boolean)
    mail_use_ssl = db.Column(db.Boolean)
    mail_debug = db.Column(db.Boolean)
    mail_username = db.Column(db.String(128))
    mail_password = db.Column(db.String(128))
    mail_default_sender = db.Column(db.String(128))
    mail_max_emails = db.Column(db.Integer)
    mail_suppress_send = db.Column(db.Boolean)
    mail_ascii_attachments = db.Column(db.Boolean)
    posts_per_page = db.Column(db.Integer)
    allowed_extensions = db.Column(db.String(128))
    ticket_upload_folder = db.Column(db.String(128))
    avatar_upload_folder = db.Column(db.String(128))
    application_title = db.Column(db.String(128))
    base_url = db.Column(db.String(128))
    auth_domain = db.Column(db.String(128))
    use_auth_domain = db.Column(db.Boolean)
    csv_dump_limit = db.Column(db.Integer)
    change_category = db.Column(db.Boolean)
    change_category_only_admin_or_super_user = db.Column(db.Boolean)
