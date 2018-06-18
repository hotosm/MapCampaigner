import os
import flask_debugtoolbar
from flask import Flask
from raven.contrib.flask import Sentry
from flask_profiler import Profiler

from app_config import Config

from campaign_manager.context_processor import inject_oauth_param
from app_sockets import osm_app
from campaign_manager import campaign_manager
from campaign_manager.views import not_found_page, forbidden_page
from campaign_manager.context_processor import inject_oauth_param
from app_config import Config
from app_sockets import osm_app

osm_app.register_blueprint(campaign_manager)


try:
    osm_app.config.from_object(os.environ['APP_SETTINGS'])
    print('config %s ' % osm_app.config['DEBUG'])
except KeyError:
    from app_config import DevelopmentConfig

    osm_app.config.from_object(DevelopmentConfig)


# Setting up Sentry
sentry = Sentry(osm_app, dsn=Config.SENTRY_DSN)


# Setup for flask-profiler
profiler = Profiler()
profiler.init_app(osm_app)
osm_app.config["flask_profiler"] = {
    "enabled": True,
    "storage": {
        "engine": "sqlite"
    },
    "basicAuth": {
        "enabled": True,
        "username": "admin",
        "password": "admin"
    },
    "ignore": [
        "^/static/.*"
    ]
}

if osm_app.config['DEBUG']:
    """Line-Profiler will not be active in deployment."""
    osm_app.config['DEBUG_TB_PANELS'] = [
            'flask_debugtoolbar.panels.versions.VersionDebugPanel',
            'flask_debugtoolbar.panels.timer.TimerDebugPanel',
            'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
            'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
            'flask_debugtoolbar.panels.template.TemplateDebugPanel',
            'flask_debugtoolbar.panels.sqlalchemy.SQLAlchemyDebugPanel',
            'flask_debugtoolbar.panels.logger.LoggingPanel',
            'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel',
            'flask_debugtoolbar_lineprofilerpanel.panels.LineProfilerPanel'
        ]
    osm_app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
    toolbar = flask_debugtoolbar.DebugToolbarExtension(osm_app)

inject_oauth_param = osm_app.context_processor(inject_oauth_param)


@osm_app.errorhandler(404)
def not_found(error):
    return not_found_page(error)


@osm_app.errorhandler(403)
def forbidden(error):
    return forbidden_page(error)
