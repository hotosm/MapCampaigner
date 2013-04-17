# coding=utf-8
"""Test cases for the Utilities module.
:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""
import os
import ast

from reporter.test.logged_unittest import LoggedTestCase
from reporter.test.helpers import FIXTURE_PATH
from reporter.utilities import (
    split_bbox,
    get_totals,
    osm_object_contributions,
    interpolated_timeline,
    average_for_active_days,
    best_active_day,
    worst_active_day)


class UtilitiesTestCase(LoggedTestCase):
    """Test the reporting functions which are the heart of this app."""

    def test_split_bbox(self):
        """Test we can split a bounding box nicely."""
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
        """Test we can handle bad bounding boxes nicely."""
        with self.assertRaises(ValueError):
            split_bbox('invalid bbox string')

    def test_osm_building_contributions(self):
        """Test that we can obtain correct contribution counts for a file."""
        myFile = open(FIXTURE_PATH)
        myList = osm_object_contributions(myFile, tag_name="building")
        myExpectedList = ast.literal_eval(file(os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'test_data',
            'expected_osm_building_contributions.txt'
        ), 'rt').read())

        self.maxDiff = None
        print myList
        self.assertListEqual(myList, myExpectedList)

    def test_get_totals(self):
        """Test we get the proper totals from a sorted user list."""
        mySortedUserList = osm_object_contributions(open(FIXTURE_PATH),
                                                    tag_name="building")
        myWays, myNodes = get_totals(mySortedUserList)
        self.assertEquals((myWays, myNodes), (427, 52))

    def test_interpolated_timeline(self):
        """Check that we can get an interpolated timeline,"""
        myTimeline = {u'2012-12-01': 10,
                      u'2012-12-10': 1}
        myExpectedResult = ('[["2012-12-01",10],'
                            '["2012-12-02",0],'
                            '["2012-12-03",0],'
                            '["2012-12-04",0],'
                            '["2012-12-05",0],'
                            '["2012-12-06",0],'
                            '["2012-12-07",0],'
                            '["2012-12-08",0],'
                            '["2012-12-09",0],'
                            '["2012-12-10",1]]')
        myResult = interpolated_timeline(myTimeline)
        self.maxDiff = None
        self.assertEqual(myExpectedResult, myResult)

    def test_average_for_active_days(self):
        """Check that we can determine the average per day."""
        myTimeline = {u'2012-12-01': 10,
                      u'2012-12-10': 1}
        myExpectedResult = 5
        myResult = average_for_active_days(myTimeline)
        self.assertEqual(myExpectedResult, myResult)

    def test_best_active_day(self):
        """Check that we can determine the best active day."""
        myTimeline = {u'2012-12-01': 10,
                      u'2012-12-10': 1}
        myExpectedResult = 10
        myResult = best_active_day(myTimeline)
        self.assertEqual(myExpectedResult, myResult)

    def test_worst_active_day(self):
        """Check that we can determine the worst active day."""
        myTimeline = {u'2012-12-01': 10,
                      u'2012-12-10': 1}
        myExpectedResult = 1
        myResult = worst_active_day(myTimeline)
        self.assertEqual(myExpectedResult, myResult)
