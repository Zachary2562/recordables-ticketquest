import os
import platform

basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfiguration(object):
    DEBUG = True
    TESTING = False
    EXPLAIN_TEMPLATE_LOADING = False

    # ----- SQLite ONLY -----
    db_name = 'flicket.db'
    sql_os_path_prefix = '////'
    if platform.system() == 'Windows':
        sql_os_path_prefix = '///'
    db_path = os.path.join(basedir, db_name)
    SQLALCHEMY_DATABASE_URI = f'sqlite:{sql_os_path_prefix}{db_path}'

    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # Basic secret key for dev. Change this in production!
    SECRET_KEY = 'dev_secret_key'

    # The base url for your application.
    WEBHOME = '/'
    FLICKET = WEBHOME + ''
    FLICKET_API = WEBHOME + 'flicket-api/'
    FLICKET_REST_API = WEBHOME + 'flicket-rest-api'
    ADMINHOME = '/flicket_admin/'

    # Use new app name in the config!
    application_title = 'Recordables and TicketQuest™'

    # ---- ADD THESE LINES FOR GROUP NAMES ----
    ADMIN_GROUP_NAME = 'flicket_admin'
    SUPER_USER_GROUP_NAME = 'super_user'
    # -----------------------------------------

    # flicket user used to post replies to tickets for status changes.
    NOTIFICATION = {'name': 'notification',
                    'username': 'notification',
                    'password': 'changeme',
                    'email': 'admin@localhost'}

    SUPPORTED_LANGUAGES = {'en': 'English', 'fr': 'Francais'}
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'US/Eastern'

    # Email configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'recordablesticketquest@gmail.com'
    MAIL_PASSWORD = 'ymra bdxk uduu dpna'
    MAIL_DEFAULT_SENDER = 'recordablesticketquest@gmail.com'

class TestConfiguration(BaseConfiguration):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'test.db')
    WTF_CSRF_ENABLED = False
    TESTING = True
    SESSION_PROTECTION = None
    LOGIN_DISABLED = False
    SERVER_NAME = 'localhost:5001'
    config_data = {"db_username": "", "db_port": "", "db_password": "",
                   "db_name": "", "db_url": ""}
