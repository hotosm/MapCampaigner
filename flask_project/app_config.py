import os
from dotenv import load_dotenv
from pathlib import Path
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

DATA_FOLDER = os.environ.get('DATA_FOLDER', '/home/web/field-campaigner-data')


class Config(object):
    """Configuration environment for application.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY', '')
    DEBUG = os.environ.get('DEBUG', False)
    TESTING = os.environ.get('TESTING', False)
    CSRF_ENABLED = os.environ.get('CSRF_ENABLED', False)

    # OSMCHA ATTRIBUTES
    _OSMCHA_DOMAIN = os.environ.get('_OSMCHA_DOMAIN', '')
    OSMCHA_API = _OSMCHA_DOMAIN + os.environ.get('OSMCHA_API_PATH', '')
    OSMCHA_FRONTEND_URL = os.environ.get('OSMCHA_FRONTEND_URL', '')

    AWS_BUCKET = os.environ.get('AWS_BUCKET', '')
    ENV = os.environ.get('ENV', '')

    # CAMPAIGN DATA
    campaigner_data_folder = DATA_FOLDER
