from flask import Flask
from reporter import reporter
from campaign_manager import campaign_manager

osm_app = Flask(__name__, static_folder='./reporter/static')
osm_app.register_blueprint(reporter)
osm_app.register_blueprint(campaign_manager, url_prefix='/campaign_manager')
