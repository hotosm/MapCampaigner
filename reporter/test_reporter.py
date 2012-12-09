# -*- coding: utf-8 -*-
"""
    Reporter Tests

    Tests the Flaskr application.

    :copyright: (c) 2010 by Tim Sutton
    :license: GPLv3, see LICENSE for more details.
"""
import reporter
import unittest


class ReporterTestCase(unittest.TestCase):

    def setUp(self):
        reporter.app.config['TESTING'] = True
        self.app = reporter.app.test_client()

    def tearDown(self):
        pass

    def test_current_status(self):
        return self.app.post('/', data=dict(), follow_redirects=True)

if __name__ == '__main__':
    unittest.main()
