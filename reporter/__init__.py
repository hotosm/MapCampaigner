import logging

from flask import Flask

from reporter.logger import setup_logger

setup_logger()
LOGGER = logging.getLogger('osm-reporter')

app = Flask(__name__)
# Don't import actual view methods themselves - see:
# http://flask.pocoo.org/docs/patterns/packages/#larger-applications
# Also views must be imported AFTER app is created above.
import reporter.views
