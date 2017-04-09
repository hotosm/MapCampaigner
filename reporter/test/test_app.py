# coding=utf-8
"""Tests for the application web urls.
:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""
from reporter.views import app
from reporter.test.logged_unittest import LoggedTestCase
from reporter import LOGGER


class AppTestCase(LoggedTestCase):
    """Test the application."""
    def setUp(self):
        """Constructor."""
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        """Destructor."""
        pass

    def test_home(self):
        """Test the home page works."""
        try:
            result = self.app.get(
                '/', data=dict(), follow_redirects=True)
            code = result.status_code
            self.assertEquals(code, 200)
        except Exception as e:
            LOGGER.exception('Basic front page load failed.')
            raise e
