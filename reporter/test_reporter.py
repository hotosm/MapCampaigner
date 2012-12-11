# -*- coding: utf-8 -*-
"""
    Reporter Tests

    Tests the Flaskr application.

    :copyright: (c) 2010 by Tim Sutton
    :license: GPLv3, see LICENSE for more details.
"""
import unittest

from reporter.core import split_bbox, app


class ReporterTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_current_status(self):
        return self.app.post('/', data=dict(), follow_redirects=True)


class UtilsTestCase(unittest.TestCase):

    def test_split_bbox(self):
        self.assertEqual(
            split_bbox("106.78674459457397,-6.141301491467023,106.80691480636597,-6.133834354201348"),
            {
                'SW_lng': 106.78674459457397,
                'SW_lat': -6.141301491467023,
                'NE_lng': 106.80691480636597,
                'NE_lat': -6.133834354201348
            }
        )

    def test_split_bad_bbox(self):
        with self.assertRaises(ValueError):
            split_bbox('invalid bbox string')


if __name__ == '__main__':
    unittest.main()
