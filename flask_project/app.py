import os
from flask import Flask
from reporter import reporter
from campaign_manager import campaign_manager
from campaign_manager.views import not_found_in_campaign
from flask import render_template

osm_app = Flask(__name__, static_folder='./reporter/static')
osm_app.register_blueprint(reporter)
osm_app.register_blueprint(campaign_manager, url_prefix='/campaign_manager')

try:
    osm_app.config.from_object(os.environ['APP_SETTINGS'])
except KeyError:
    from app_config import DevelopmentConfig

    osm_app.config.from_object(DevelopmentConfig)


@osm_app.errorhandler(404)
def not_found(error):
    return not_found_in_campaign(error)
