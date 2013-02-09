import logging
import os

from reporter.logger import setup_logger

setup_logger()
LOGGER = logging.getLogger('osm-reporter')

FIXTURE_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'test_data',
    'swellendam.osm'
)
