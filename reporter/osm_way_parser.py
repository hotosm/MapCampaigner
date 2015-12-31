# coding=utf-8
"""Module for parsing ways from OSM xml documents.
:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""
import xml.sax


class OsmParser(xml.sax.ContentHandler):
    """Sax parser for an OSM xml document.

    Sax is used so that large documents can be parsed efficiently.
    """

    def __init__(self, tagName):
        """Constructor for parser.

        Args:
            tagName: str - the name of the osm tag to use for parsing e.g.
            'buildings' or 'roads'.

        Returns:
            OsmParser instance.
        Raises:
            None

        """
        xml.sax.ContentHandler.__init__(self)
        self.wayCount = 0
        self.nodeCount = 0
        self.inWay = False
        self.user = None
        self.found = False  # mark when object found
        self.tagName = tagName
        self.wayCountDict = {}
        self.nodeCountDict = {}
        self.userDayCountDict = {}

    def startElement(self, name, attributes):
        """Callback for when an element start is encountered.

        :param name: The name of the element.
        :type name: str

        :param attributes: dict - collection of key, value pairs representing
                the attributes of the element.
        :type attributes: OsmParser
        """
        if name == 'way':
            self.inWay = True
            self.wayCount += 1
            self.user = attributes.getValue('user')
            timestamp = attributes.getValue('timestamp')
            # 2012-12-10T12:26:21Z
            date_part = timestamp.split('T')[0]
            if self.user not in self.userDayCountDict:
                self.userDayCountDict[self.user] = dict()

            if date_part not in self.userDayCountDict[self.user]:
                self.userDayCountDict[self.user][date_part] = 0

            value = self.userDayCountDict[self.user][date_part]
            value += 1
            self.userDayCountDict[self.user][date_part] = value

        elif name == 'nd' and self.inWay:
            self.nodeCount += 1

        elif name == 'tag' and self.inWay:
            if attributes.getValue('k') == self.tagName:
                self.found = True

        else:
            pass
            # print 'Node not known %s' % name

    def endElement(self, name):
        """Callback for when an element start is encountered.

        :param name: The name of the element that has ended.
        :type name: str
        """
        if name == 'way':
            if self.found:
                # Its a target object so update it and node counts
                if self.user in self.wayCountDict:
                    myValue = self.wayCountDict[self.user]
                    self.wayCountDict[self.user] = myValue + 1
                    myValue = self.nodeCountDict[self.user]
                    self.nodeCountDict[self.user] = myValue + self.nodeCount
                else:
                    self.wayCountDict[self.user] = 1
                    self.nodeCountDict[self.user] = self.nodeCount

            self.inWay = False
            self.user = None
            self.found = False
            self.nodeCount = 0
            self.wayCount = 0

    def characters(self, content):
        """Return chars from content - unimplmented.

        :param content: Unused node element.
        :type content: node

        """
        pass
