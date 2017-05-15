import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from reporter import reporter
from campaign_manager import campaign_manager
import utilities

osm_app = Flask(__name__, static_folder='./reporter/static')
osm_app.register_blueprint(reporter)
osm_app.register_blueprint(campaign_manager, url_prefix='/campaign_manager')
osm_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

try:
    osm_app.config.from_object(os.environ['APP_SETTINGS'])
except KeyError:
    from app_config import DevelopmentConfig
    osm_app.config.from_object(DevelopmentConfig)

db = SQLAlchemy(osm_app)

from campaign_manager.models import OsmUser
