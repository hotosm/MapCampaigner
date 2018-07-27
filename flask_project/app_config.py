import os

# import SECRET_KEY into current namespace
# noinspection PyUnresolvedReferences
try:
    from secret import SECRET_KEY as THE_SECRET_KEY  # noqa
except ImportError:
    THE_SECRET_KEY = os.environ['SECRET_KEY']
try:
    DATA_FOLDER = os.environ['DATA_FOLDER']
except KeyError:
    DATA_FOLDER = '/home/web/field-campaigner-data'


class Config(object):
    """Configuration environment for application.
    """
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = THE_SECRET_KEY

    # OSMCHA ATTRIBUTES
    _OSMCHA_DOMAIN = 'https://osmcha.mapbox.com/'
    OSMCHA_API = _OSMCHA_DOMAIN + 'api/v1/'
    OSMCHA_FRONTEND_URL = 'https://osmcha.mapbox.com/'

    # CAMPAIGN DATA
    campaigner_data_folder = DATA_FOLDER


class ProductionConfig(Config):
    """Production environment.
    """
    DEBUG = False
    AWS_BUCKET = 'fieldcampaigner-data-production'


class AWSProductionConfig(Config):
    """
    AWS Production environment in HOTOSM AWS account.
    """
    DEBUG = False
    AWS_BUCKET = 'hotosm-fieldcampaigner-data-production'


class StagingConfig(Config):
    """Staging environment.
    """
    DEVELOPMENT = True
    DEBUG = True
    AWS_BUCKET = 'fieldcampaigner-data-staging'


class AWSStagingConfig(Config):
    """
    AWS Staging environment in HOTOSM AWS account.
    """
    DEVELOPMENT = True
    DEBUG = True
    AWS_BUCKET = 'hotosm-fieldcampaigner-data-staging'


class DevelopmentConfig(Config):
    """Development environment.
    """
    DEVELOPMENT = True
    DEBUG = True
    AWS_BUCKET = 'fieldcampaigner-data'


class TestingConfig(Config):
    """
    Testing environment.
    """
    TESTING = True
    DEBUG = True
    AWS_BUCKET = 'fieldcampaigner-data-test'


class AWSTestingConfig(Config):
    """
    AWS Testing environment in HOTOSM AWS account.
    """
    TESTING = True
    DEBUG = True
    AWS_BUCKET = 'hotosm-fieldcampaigner-data-test'
