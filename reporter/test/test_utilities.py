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
        message = 'test_split_box failed.'
        self.assertEqual(
            split_bbox('106.78674459457397,-6.141301491467023,'
                       '106.80691480636597,-6.133834354201348'),
            {
                'SW_lng': 106.78674459457397,
                'SW_lat': -6.141301491467023,
                'NE_lng': 106.80691480636597,
                'NE_lat': -6.133834354201348
            },
            message
        )

    def test_split_bad_bbox(self):
        """Test we can handle bad bounding boxes nicely."""
        with self.assertRaises(ValueError):
            split_bbox('invalid bbox string')

    def test_osm_building_contributions(self):
        """Test that we can obtain correct contribution counts for a file."""
        file_handle = open(FIXTURE_PATH)
        contributor_list = osm_object_contributions(
            file_handle,
            tag_name="building")
        expected_list = ast.literal_eval(file(os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'test_data',
            'expected_osm_building_contributions.txt'
        )).read())

        #noinspection PyPep8Naming
        self.maxDiff = None
        print contributor_list
        self.assertListEqual(contributor_list, expected_list)

    def test_get_totals(self):
        """Test we get the proper totals from a sorted user list."""
        sorted_user_list = osm_object_contributions(
            open(FIXTURE_PATH),
            tag_name="building")
        ways, nodes = get_totals(sorted_user_list)
        self.assertEquals((ways, nodes), (427, 52))

    def test_interpolated_time_line(self):
        """Check that we can get an interpolated time_line,"""
        time_line = {
            u'2012-12-01': 10,
            u'2012-12-10': 1}
        expected_result = (
            '[["2012-12-01",10],'
            '["2012-12-02",0],'
            '["2012-12-03",0],'
            '["2012-12-04",0],'
            '["2012-12-05",0],'
            '["2012-12-06",0],'
            '["2012-12-07",0],'
            '["2012-12-08",0],'
            '["2012-12-09",0],'
            '["2012-12-10",1]]')
        result = interpolated_timeline(time_line)
        #noinspection PyPep8Naming
        self.maxDiff = None
        self.assertEqual(expected_result, result)

    def test_average_for_active_days(self):
        """Check that we can determine the average per day."""
        time_line = {
            u'2012-12-01': 10,
            u'2012-12-10': 1}
        expected_result = 5
        result = average_for_active_days(time_line)
        self.assertEqual(expected_result, result)

    def test_best_active_day(self):
        """Check that we can determine the best active day."""
        time_line = {
            u'2012-12-01': 10,
            u'2012-12-10': 1}
        expected_result = 10
        result = best_active_day(time_line)
        self.assertEqual(expected_result, result)

    def test_worst_active_day(self):
        """Check that we can determine the worst active day."""
        time_line = {
            u'2012-12-01': 10,
            u'2012-12-10': 1}
        expected_result = 1
        result = worst_active_day(time_line)
        self.assertEqual(expected_result, result)
