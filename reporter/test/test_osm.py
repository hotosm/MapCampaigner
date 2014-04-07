# coding=utf-8
"""Test cases for the OSM module.
:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""
import os

from reporter.utilities import LOGGER
from reporter.osm import (
    load_osm_document,
    extract_buildings_shapefile,
    extract_roads_shapefile,
    check_string)
from reporter.test.helpers import FIXTURE_PATH

from reporter.test.logged_unittest import LoggedTestCase


class OsmTestCase(LoggedTestCase):
    """Test the OSM retrieval functions."""

    def test_load_osm_document(self):
        """Check that we can fetch an osm doc and that it caches properly."""
        #
        # NOTE - INTERNET CONNECTION NEEDED FOR THIS TEST
        #
        url = (
            'http://overpass-api.de/api/interpreter?data='
            '(node(-34.03112731086964,20.44997155666351,'
            '-34.029571310785315,20.45501410961151);<;);out+meta;')
        file_path = '/tmp/test_load_osm_document.osm'
        if os.path.exists(file_path):
            os.remove(file_path)
            # We test twice - once to ensure its fetched from the overpass api
        # and once to ensure the cached file is used on second access
        # Note: There is a small chance the second test could fail if it
        # exactly straddles the cache expiry time.
        try:
            file_handle = load_osm_document(file_path, url)
        except:
            message = 'load_osm_document from overpass failed %s' % url
            LOGGER.exception(message)
            raise
        string = file_handle.read()
        message = 'load_osm_document from overpass content check failed.'
        assert 'Jacoline' in string, message

        #file_handle = load_osm_document(myFilePath, url)
        file_time = os.path.getmtime(file_path)
        #
        # This one should be cached now....
        #
        load_osm_document(file_path, url)
        file_time2 = os.path.getmtime(file_path)
        message = 'load_osm_document cache test failed.'
        self.assertEqual(file_time, file_time2, message)

    def test_extract_buildings_shapefile(self):
        """Test the osm to shp converter."""
        zip_path = extract_buildings_shapefile(FIXTURE_PATH)
        #print zip_path
        self.assertTrue(os.path.exists(zip_path), zip_path)

    def test_extract_roads_shapefile(self):
        """Test the roads to shp converter."""
        zip_path = extract_roads_shapefile(FIXTURE_PATH)
        #print zip_path
        self.assertTrue(os.path.exists(zip_path), zip_path)

    def test_check_string(self):
        """Test that we can validate for bad strings."""
        bad_text = ['../../etc/passwd', '&^%$']
        good_text = ['roads', 'buildings', 'roads_12012014', 'ID_']

        for bad in bad_text:
            self.assertFalse(
                check_string(bad),
                '%s should NOT be acceptible' % bad)

        for good in good_text:
            self.assertTrue(
                check_string(good),
                '%s should be acceptible' % good)

