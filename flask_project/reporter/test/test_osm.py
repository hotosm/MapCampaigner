# coding=utf-8
"""Test cases for the OSM module.
:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""
import os

from unittest import mock
from reporter.utilities import LOGGER
from reporter.osm import (
    load_osm_document,
    import_and_extract_shapefile,
    check_string)
from reporter.test.helpers import FIXTURE_PATH

from reporter.test.logged_unittest import LoggedTestCase


def mock_load_osm_document(file_path, url):

    if file_path == '/tmp/test_load_osm_document.osm' \
            and url == 'http://overpass-api.de/api/interpreter?data=(' \
                    'node(-34.03112731086964,20.44997155666351,' \
                    '-34.029571310785315,20.45501410961151);<;);out+meta;':
        return 'overpass success'

    return None


def mock_open(file_path, string):

    if file_path == '/tmp/test_load_osm_document.osm':
        return 'success'
    elif file_path == '/tmp/test_load_osm_document_with_Date.osm':
        return 'success with date'
    return None


def mock_getmtime(file_path):

    if file_path == '/tmp/test_load_osm_document.osm':
        return 'osm document loaded'

    return None


def mock_which(name, flags=os.X_OK):

    if(name):
        result = ['found1', 'found2']

    return result


class OsmTestCase(LoggedTestCase):
    """Test the OSM retrieval functions."""

    @mock.patch('reporter.osm.open', side_effect=mock_open)
    @mock.patch('reporter.osm.fetch_osm', side_effect=mock_load_osm_document)
    @mock.patch('os.path.getmtime', side_effect=mock_getmtime)
    def test_load_osm_document(self, mock_open_file, mock_fetch_osm, mock_get_mtime):
        """Check that we can fetch an osm doc and that it caches properly."""

        url = (
            'http://overpass-api.de/api/interpreter?data='
            '(node(-34.03112731086964,20.44997155666351,'
            '-34.029571310785315,20.45501410961151);<;);out+meta;')
        file_path = '/tmp/test_load_osm_document.osm'
        LOGGER.info('url: %s' % url)
        LOGGER.info('file_path: %s' % file_path)
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
        # string = file_handle.read().decode('utf-8')
        LOGGER.info('Checking that Jacoline is in the returned document...')
        # self.assertIn('Jacoline', file_handle)
        self.assertIsNotNone(file_handle)
        self.assertEquals(file_handle, 'success')
        LOGGER.info('....OK')
        # file_handle = load_osm_document(myFilePath, url)
        file_time = os.path.getmtime(file_path)
        #
        # This one should be cached now....
        #
        load_osm_document(file_path, url)
        file_time2 = os.path.getmtime(file_path)
        message = 'load_osm_document cache test failed.'
        LOGGER.info('Checking that downloaded file has a recent timestamp...')
        self.assertEqual(file_time, file_time2, message)
        LOGGER.info('....OK')

    @mock.patch('reporter.osm.open', side_effect=mock_open)
    @mock.patch('reporter.osm.fetch_osm', side_effect=mock_load_osm_document)
    @mock.patch('os.path.getmtime', side_effect=mock_getmtime)
    def test_get_osm_file_with_date_range(self, mock_open_file, mock_fetch_osm, mock_get_mtime):
        """Check that we can get osm file with date range as query"""

        url = (
            'http://overpass-api.de/api/interpreter?data='
            '[diff:"2012-09-14T15:00:00Z","2015-09-21T15:00:00Z"];'
            '(node(-34.03112731086964,20.44997155666351,'
            '-34.029571310785315,20.45501410961151);<;);out+meta;')
        file_path = '/tmp/test_load_osm_document_with_Date.osm'
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
        # string = file_handle.read().decode('utf-8')
        LOGGER.info('Checking that Jacoline is in the returned document...')
        # self.assertIn('Jacoline', string)
        self.assertIsNotNone(file_handle)
        self.assertEquals(file_handle, 'success with date')
        file_time = os.path.getmtime(file_path)
        #
        # This one should be cached now....
        #
        load_osm_document(file_path, url)
        file_time2 = os.path.getmtime(file_path)
        message = 'load_osm_document cache test failed.'
        LOGGER.info('Checking that downloaded file has a recent timestamp...')
        self.assertEqual(file_time, file_time2, message)
        LOGGER.info('....OK')

    @mock.patch('reporter.osm.which', side_effect=mock_which)
    def test_import_and_extract_shapefile(self, mock):
        """Test the roads to shp converter."""
        zip_path = import_and_extract_shapefile('buildings', FIXTURE_PATH)
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
