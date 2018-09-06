# coding=utf-8
"""Test cases for the OSM Way Parser module.
:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""
import xml
import unittest

from reporter.test.logged_unittest import LoggedTestCase
from reporter.osm_way_parser import OsmParser
from reporter.test.helpers import FIXTURE_PATH


class OsmParserTestCase(LoggedTestCase):
    """Test the sax parser for OSM data."""

    def test_parse(self):
        """Test that we can parse a predefined osm file."""
        parser = OsmParser(tag_name="amenity")
        source = open(FIXTURE_PATH)
        xml.sax.parse(source, parser)

        expected_way_dict = {u'visana': 1,
                             u'Hanif Al Husaini': 1,
                             u'indomapper': 5,
                             u'b-ghost': 1,
                             u'lek_dodok': 2}

        # OsmParser way count test
        self.assertDictEqual(expected_way_dict, parser.wayCountDict)


if __name__ == '__main__':
    unittest.main()
