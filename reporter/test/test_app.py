from reporter.views import app
from reporter.test.logged_unittest import LoggedTestCase
from reporter.test.helpers import LOGGER


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
