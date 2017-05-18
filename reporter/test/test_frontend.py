# coding=utf-8
import os
import unittest
from urllib import request
import time

from selenium import webdriver
from selenium.webdriver.support.ui import Select

from reporter.test.logged_unittest import LoggedLiveServerTestCase
from reporter import LOGGER


class TestFrontEnd(LoggedLiveServerTestCase):
    """Run front end tests using selenium.

    See this url for a very nice article explaining how the selenium
    testing logic works:

    https://scotch.io/tutorials/test-a-flask-app-with-selenium-webdriver-part-1
    """

    def setUp(self):
        """Setup the selenium driver."""
        self.app = self.create_app()
        # First just do a basic test to see that the test server works
        # independently of selenium tests.
        # result = self.app.get(
        #    '/', data=dict(), follow_redirects=True)
        # code = result.status_code
        # self.assertEquals(code, 200)

        # now setup selenium driver
        # TODO add platform check and look for common browsers
        # We can check firefox and chrome on all platforms...
        try:
            self.driver = webdriver.Chrome()
        except Exception as e:
            self.fail(
                'Error setting up selenium driver for Chrome\n%s' % e.message)
        try:
            self.driver.get(self.get_server_url())
        except Exception as e:
            self.fail(
                'Error getting server url for selenium tests\n%s' % e.message)
        LOGGER.info('Preparing to run front end tests')

    def tearDown(self):
        """Clean up the selenium driver."""
        self.driver.quit()

    # I am awaiting saucelabs problem resolution with my account before
    # we can set up travis + selenium builds
    @unittest.skipIf(
        os.environ.get('ON_TRAVIS', False),
        'This test is not set up for travis yet.')
    def test_server_is_up_and_running(self):
        """Check that the home page loads ok."""
        response = request.urlopen(self.get_server_url())
        self.assertEqual(response.code, 200)

    # I am awaiting saucelabs problem resolution with my account before
    # we can set up travis + selenium builds
    @unittest.skipIf(
        os.environ.get('ON_TRAVIS', False),
        'This test is not set up for travis yet.')
    def test_roads(self):
        """Check that when we switch to roads the report updates."""

        select_feature_type = Select(
            self.driver.find_element_by_id('feature_select'))
        select_feature_type.select_by_visible_text('highway')
        time.sleep(1)

        text = self.driver.find_element_by_id('report-heading').text
        self.assertEqual('Highway Contributors', text)

    # I am awaiting saucelabs problem resolution with my account before
    # we can set up travis + selenium builds
    @unittest.skipIf(
        os.environ.get('ON_TRAVIS', False),
        'This test is not set up for travis yet.')
    def test_buildings(self):
        """Check that when we switch to buildings the report updates."""

        select_feature_type = Select(
            self.driver.find_element_by_id('feature_select'))
        select_feature_type.select_by_visible_text('building')

        self.driver.find_element_by_id('refresh-with-date').click()
        time.sleep(1)

        text = self.driver.find_element_by_id('report-heading').text
        self.assertEqual('Building Contributors', text)

    # I am awaiting saucelabs problem resolution with my account before
    # we can set up travis + selenium builds
    @unittest.skipIf(
        os.environ.get('ON_TRAVIS', False),
        'This test is not set up for travis yet.')
    def test_evacuation_centers(self):
        """Check that when switch to evacuation centers the report updates."""

        select_feature_type = Select(
            self.driver.find_element_by_id('feature_select'))
        select_feature_type.select_by_visible_text('evacuation_center')

        self.driver.find_element_by_id('refresh-with-date').click()
        time.sleep(1)

        text = self.driver.find_element_by_id('report-heading').text
        self.assertEqual('Evacuation center Contributors', text)

    # I am awaiting saucelabs problem resolution with my account before
    # we can set up travis + selenium builds
    @unittest.skipIf(
        os.environ.get('ON_TRAVIS', False),
        'This test is not set up for travis yet.')
    def test_flood_prone(self):
        """Check that when switch to flood_prone the report updates."""

        select_feature_type = Select(
            self.driver.find_element_by_id('feature_select'))
        select_feature_type.select_by_visible_text('flood_prone')

        self.driver.find_element_by_id('refresh-with-date').click()
        time.sleep(1)

        text = self.driver.find_element_by_id('report-heading').text
        self.assertEqual('Flood prone Contributors', text)

if __name__ == '__main__':
    unittest.main()
