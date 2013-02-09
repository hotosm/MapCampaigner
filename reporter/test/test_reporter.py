# -*- coding: utf-8 -*-
"""
    Reporter Tests

    Tests the osm-reporter application.

    :copyright: (c) 2010 by Tim Sutton
    :license: GPLv3, see LICENSE for more details.
"""
import unittest

from reporter.utilities import split_bbox
from reporter.test.logged_unittest import LoggedTestCase


class UtilitiesTestCase(LoggedTestCase):
    """Tests for the utilities module."""
    def test_split_bbox(self):
        myMessage = 'test_split_box failed.'
        self.assertEqual(
            split_bbox('106.78674459457397,-6.141301491467023,'
                       '106.80691480636597,-6.133834354201348'),
            {
                'SW_lng': 106.78674459457397,
                'SW_lat': -6.141301491467023,
                'NE_lng': 106.80691480636597,
                'NE_lat': -6.133834354201348
            },
            myMessage
        )

    def test_split_bad_bbox(self):
        with self.assertRaises(ValueError):
            split_bbox('invalid bbox string')


if __name__ == '__main__':
    unittest.main()
