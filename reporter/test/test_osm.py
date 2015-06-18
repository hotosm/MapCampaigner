# coding=utf-8
"""Test cases for the OSM module.
:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""
import os

from reporter.utilities import LOGGER
from reporter.osm import (
    load_osm_document,
    extract_shapefile,
    short_version,
    latest_xml_metadata_file,
    metadata_file,
    metadata_files,
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

    def test_latest_xml_metadata_file(self):
        """Test the maximum version available of an XML keyword file."""
        self.assertTrue(latest_xml_metadata_file('building-points') == 3.2)
        self.assertTrue(latest_xml_metadata_file('buildings') == 3.2)
        self.assertTrue(latest_xml_metadata_file('roads') == 3.2)

    def test_metadata_file(self):
        """Test we get the good metadata file."""
        file_suffix = metadata_file('keywords', '3.1', 'fake_lang', 'roads')
        self.assertEqual('-en.keywords', file_suffix)

        file_suffix = metadata_file('keywords', None, 'fr', 'roads')
        self.assertEqual('-fr.keywords', file_suffix)

        file_suffix = metadata_file('xml', '3.3', 'fake_lang', 'roads')
        self.assertEqual('-3.2-en.xml', file_suffix)

        file_suffix = metadata_file('xml', '3.2', 'en', 'roads')
        self.assertEqual('-3.2-en.xml', file_suffix)

    def test_metadata_files(self):
        """Test we get all metadata files."""
        metadata = metadata_files('3.2', 'en', 'roads', 'test')
        expected_metadata = {'test.xml': '-3.2-en.xml'}
        self.assertDictEqual(expected_metadata, metadata)

        metadata = metadata_files(None, 'fr', 'roads', 'test')
        expected_metadata = {
            'test.xml': '-3.2-en.xml',
            'test.keywords': '-fr.keywords'
        }
        self.assertDictEqual(expected_metadata, metadata)

        metadata = metadata_files('3.1', 'en', 'roads', 'test')
        expected_metadata = {'test.keywords': '-en.keywords'}
        self.assertDictEqual(expected_metadata, metadata)

    def test_short_version(self):
        """Test the inasafe version."""
        self.assertEquals(short_version('3.2.0.dev-dbb84de'), 3.2)
        self.assertEquals(short_version('3.2.0'), 3.2)
        self.assertEquals(short_version('3.2'), 3.2)

    def test_extract_shapefile(self):
        """Test the roads to shp converter."""
        zip_path = extract_shapefile('buildings', FIXTURE_PATH)
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
