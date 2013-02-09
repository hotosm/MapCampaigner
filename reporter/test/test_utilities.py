import os
import ast

from reporter.test.logged_unittest import LoggedTestCase
from reporter.test.helpers import FIXTURE_PATH
from reporter.utilities import (
    get_totals,
    osm_object_contributions,
    interpolated_timeline)


class UtilitiesTestCase(LoggedTestCase):
    """Test the reporting functions which are the heart of this app."""

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
