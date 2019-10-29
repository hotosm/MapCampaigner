import os
from flask import Flask
from campaign_manager import campaign_manager
from campaign_manager.views import not_found_page, forbidden_page

osm_app = Flask(__name__, static_folder='./campaign_manager/static')
osm_app.register_blueprint(campaign_manager)

try:
    osm_app.config.from_object(os.environ['APP_SETTINGS'])

    print('config %s ' % osm_app.config['DEBUG'])
except KeyError:
    from app_config import Config

    osm_app.config.from_object(Config)


@osm_app.errorhandler(404)
def not_found(error):
    return not_found_page(error)


@osm_app.errorhandler(403)
def forbidden(error):
    return forbidden_page(error)
