import os

# import SECRET_KEY into current namespace
# noinspection PyUnresolvedReferences
try:
    from secret import SECRET_KEY as THE_SECRET_KEY  # noqa
    from secret import OAUTH_CONSUMER_KEY, OAUTH_SECRET, SENTRY_DSN
except ImportError as e:
    THE_SECRET_KEY = ''
    OAUTH_CONSUMER_KEY = ''
    OAUTH_SECRET = ''
    SENTRY_DSN = ''

DATABASEURL = 'postgres://docker:docker@localhost:4000/gis'


class Config(object):
    """Configuration environment for application.
    """
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = THE_SECRET_KEY
    OAUTH_CONSUMER_KEY = OAUTH_CONSUMER_KEY
    OAUTH_SECRET = OAUTH_SECRET
    SENTRY_DSN = SENTRY_DSN
    MAX_AREA_SIZE = 320000000
    DB_LOCATION = DATABASEURL

    # OSMCHA ATTRIBUTES
    _OSMCHA_DOMAIN = 'https://osmcha.mapbox.com/'
    OSMCHA_API = _OSMCHA_DOMAIN + 'api/v1/'
    OSMCHA_FRONTEND_URL = 'https://osmcha.mapbox.com/'

    # OVERPASS ATTRIBUTES
    ATTIC_DATA_SERVER_URL = 'http://ec2-54-172-198-122.compute-1.amazonaws.com/api/interpreter'
    DEFAULT_OVERPASS_URL = 'http://exports-prod.hotosm.org:6080/api/interpreter'

    # CAMPAIGN DATA
    campaigner_data_folder = "./campaign_manager/static"


class ProductionConfig(Config):
    """Production environment.
    """
    DEBUG = False


class StagingConfig(Config):
    """Staging environment.
    """
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    """Development environment.
    """
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    """Testing environment.
    """
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = True
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    DB_LOCATION = 'postgres://docker:docker@localhost:4001/gis'
    DRIVER_PATH = os.path.abspath('./campaign_manager/test/chromedriver')
