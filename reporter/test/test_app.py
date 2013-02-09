import ast
import os

from reporter.views import app
from reporter.utilities import (
    osm_object_contributions,
    get_totals,
    interpolated_timeline)
from reporter.test.logged_unittest import LoggedTestCase
from reporter.osm import load_osm_document
from reporter.test.helpers import LOGGER, FIXTURE_PATH


class AppTestCase(LoggedTestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_home(self):
        try:
            return self.app.post('/', data=dict(), follow_redirects=True)
        except Exception, e:
            LOGGER.exception('Basic front page load failed.')
            raise e
