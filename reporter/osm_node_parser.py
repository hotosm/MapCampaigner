# coding=utf-8
from xml import sax

"""Module for parsing nodes from OSM xml documents.
:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""


class OsmNodeParser(sax.ContentHandler):
    """SAX Parser to retrieve nodes from an OSM XML document."""

    def __init__(self, username):
        """Constructor.

        :param username: The name of the user for whom nodes should be
            retrieved.
        :type username: str

        :returns: An OsmNodeParser instance.
        :rtype: OsmNodeParser
        """
        super().__init__()
        self.username = username
        # A collection of nodes that have been found for a user.
        self.nodes = []

    def startElement(self, name, attributes):
        """Callback for when an element start is encountered.

        :param name: Name of the element.
        :type name: str

        :param attributes: Collection of key, value pairs representing
                the attributes of the element.
        :type attributes: node
        """
        if name == 'node':
            if attributes.getValue('user') == self.username:
                self.nodes.append((
                    float(attributes.getValue('lat')),
                    float(attributes.getValue('lon'))))
