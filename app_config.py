import os
# import SECRET_KEY into current namespace
# noinspection PyUnresolvedReferences
try:
    from secret import SECRET_KEY as THE_SECRET_KEY  # noqa
except ImportError:
    THE_SECRET_KEY = os.environ['SECRET_KEY']


class Config(object):
    """Configuration environment for application.
    """
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = THE_SECRET_KEY
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']


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
