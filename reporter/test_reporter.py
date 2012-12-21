# -*- coding: utf-8 -*-
"""
    Reporter Tests

    Tests the osm-reporter application.

    :copyright: (c) 2010 by Tim Sutton
    :license: GPLv3, see LICENSE for more details.
"""
import os
import unittest
import xml.sax
import logging
import logging.handlers

from core import (split_bbox,
                           app,
                           setupLogger,
                           get_totals,
                           osm_building_contributions,
                           load_osm_document)
from osm_parser import OsmParser


setupLogger()
LOGGER = logging.getLogger('osm-reporter')

FIXTURE_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'test_data',
    'swellendam.osm'
)

class TestCaseLogger(unittest.TestCase):

    def failureException(self, msg):
        LOGGER.exception(msg)
        return self.super(TestCaseLogger, self).failureException(msg)

class CoreTestCase(TestCaseLogger):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_current_status(self):
        try:
            return self.app.post('/', data=dict(), follow_redirects=True)
        except Exception, e:
            LOGGER.exception('Basic front page load failed.')
            raise e

    def test_load_osm_document(self):
        """Check that we can fetch an osm doc and that it caches properly."""
        #
        # NOTE - INTERNET CONNECTION NEEDED FOR THIS TEST
        #
        myUrl = ('http://overpass-api.de/api/interpreter?data='
                     '(node(-34.03112731086964,20.44997155666351,'
                     '-34.029571310785315,20.45501410961151);<;);out+meta;')
        myFilePath = '/tmp/test_load_osm_document.osm'
        if os.path.exists(myFilePath):
            os.remove(myFilePath)
        # We test twice - once to ensure it is fetched from the overpass api
        # and once to ensure the cached file is used on second access
        # Note: There is a small chance the second test could fail if it
        # exactly straddles the cache expiry time.
        try:
            myFile = load_osm_document(myFilePath, myUrl)
        except:
            LOGGER.exception('load_osm_document from overpass test failed %s'
                             % myUrl)
            raise
        myString = myFile.read()
        myMessage = 'load_osm_document from overpass content check failed.'
        assert 'Jacoline' in myString, myMessage

        myFile = load_osm_document(myFilePath, myUrl)
        myFileTime = os.path.getmtime(myFilePath)
        myString = myFile.read()
        #
        # This one should be cached now....
        #
        load_osm_document(myFilePath, myUrl)
        myFileTime2 = os.path.getmtime(myFilePath)
        myMessage = 'load_osm_document cache test failed.'
        self.assertEqual(myFileTime, myFileTime2, myMessage)


    def test_osm_building_contributions(self):
        """Test that we can obtain correct contribution counts for a file."""
        myFile = open(FIXTURE_PATH)
        myList = osm_building_contributions(myFile)
        myExpectedList = [
            {'crew': False, 'name': u'Babsie', 'nodes': 306, 'ways': 37},
            {'crew': False, 'name': u'Firefishy', 'nodes': 104, 'ways': 12},
            {'crew': False, 'name': u'Jacoline', 'nodes': 17, 'ways': 3}]
        myMessage = 'osm_building_contributions test failed.'
        self.assertListEqual(myList, myExpectedList, myMessage)

    def test_get_totals(self):
        """Test we get the proper totals from a sorted user list."""
        mySortedUserList = osm_building_contributions(open(FIXTURE_PATH))
        myWays, myNodes = get_totals(mySortedUserList)
        myMessage = 'get_totals test failed.'
        self.assertEquals((myWays, myNodes), (427, 52), myMessage)


class OsmParserTestCase(TestCaseLogger):
    """Test the sax parser for OSM data."""
    def test_parse(self):
        myParser = OsmParser()
        source = open(FIXTURE_PATH)
        xml.sax.parse(source, myParser)
        myExpectedWayDict = {u'Babsie': 37,
                             u'Firefishy': 12,
                             u'Jacoline': 3}
        myExpectedNodeDict = {u'Babsie': 306,
                              u'Firefishy': 104,
                              u'Jacoline': 17}

        myMessage = 'OsmParser way count test failed.'
        self.assertDictEqual(myExpectedWayDict,
                             myParser.wayCountDict,
                             myMessage)

        myMessage = 'OsmParser node count test failed.'
        self.assertDictEqual(myExpectedNodeDict,
                             myParser.nodeCountDict,
                             myMessage)


class UtilsTestCase(TestCaseLogger):

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
