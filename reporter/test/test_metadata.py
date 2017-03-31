__author__ = 'etienne'

from reporter.metadata import (
    latest_xml_metadata_file,
    metadata_file,
    metadata_files)
from reporter.test.logged_unittest import LoggedTestCase


class OsmTestCase(LoggedTestCase):
    """Test the OSM retrieval functions."""

    def test_latest_xml_metadata_file(self):
        """Test the maximum version available of an XML keyword file."""
        self.assertTrue(latest_xml_metadata_file('building-points') == 4.0)
        self.assertTrue(latest_xml_metadata_file('buildings') == 4.0)
        self.assertTrue(latest_xml_metadata_file('roads') == 4.0)

    def test_metadata_file(self):
        """Test we get the good metadata file."""
        file_suffix = metadata_file('keywords', '3.1', 'fake_lang', 'roads')
        self.assertEqual('-en.keywords', file_suffix)

        file_suffix = metadata_file('keywords', None, 'fr', 'roads')
        self.assertEqual('-fr.keywords', file_suffix)

        file_suffix = metadata_file('xml', '99.0', 'fake_lang', 'roads')
        self.assertEqual('-4.0-en.xml', file_suffix)

        file_suffix = metadata_file('xml', '99.0', 'en', 'roads')
        self.assertEqual('-4.0-en.xml', file_suffix)

        file_suffix = metadata_file('xml', '99.0', 'fr', 'roads')
        self.assertEqual('-4.0-fr.xml', file_suffix)

        file_suffix = metadata_file('xml', '3.3', 'en', 'roads')
        self.assertEqual('-3.3-en.xml', file_suffix)

    def test_metadata_files(self):
        """Test we get all metadata files."""
        metadata = metadata_files('3.2', 'en', 'roads', 'test')
        expected_metadata = {'test.xml': '-3.2-en.xml'}
        self.assertDictEqual(expected_metadata, metadata)

        # noinspection PyTypeChecker
        metadata = metadata_files(None, 'fr', 'roads', 'test')
        expected_metadata = {
            'test.xml': '-4.0-fr.xml'
        }
        self.assertDictEqual(expected_metadata, metadata)

        metadata = metadata_files('3.1', 'fr', 'roads', 'test')
        expected_metadata = {'test.keywords': '-fr.keywords'}
        self.assertDictEqual(expected_metadata, metadata)
