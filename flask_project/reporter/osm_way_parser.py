# coding=utf-8
"""Module for parsing ways from OSM xml documents.
:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""
import calendar
import datetime
import xml.sax


class OsmParser(xml.sax.ContentHandler):
    """Sax parser for an OSM xml document.

    Sax is used so that large documents can be parsed efficiently.
    """

    def __init__(self, tag_name, start_date=None, end_date=None):
        """Constructor for parser.

        :param tag_name: Name of the osm tag to use for parsing e.g.
            'buildings' or 'roads'.
        :type tag_name: basestring
        
        :param start_date: Start date of range time to parse
        :type start_date: float
        
        :param end_date: End date of range time to parse
        :type end_date: float

        :returns: An OsmParser
        :rtype: OsmParser instance.
        """
        xml.sax.ContentHandler.__init__(self)
        self.wayCount = 0
        self.nodeCount = 0
        self.inWay = False
        self.user = None
        self.found = False  # mark when object found
        self.tagName = tag_name
        self.wayCountDict = {}
        self.nodeCountDict = {}
        self.userDayCountDict = {}
        self.ignoreOld = False
        self.dateStart = start_date
        self.dateEnd = end_date

    def startElement(self, name, attributes):
        """Callback for when an element start is encountered.

        :param name: The name of the element.
        :type name: str

        :param attributes: dict - collection of key, value pairs representing
                the attributes of the element.
        :type attributes: dict
        """
        if self.dateStart and self.dateEnd and name == 'old':
            self.ignoreOld = True

        if self.ignoreOld:
            return

        if name == 'way':
            timestamp = attributes.get('timestamp')
            # 2012-12-10T12:26:21Z
            date_part = timestamp.split('T')[0]

            if self.dateStart and self.dateEnd:
                date_timestamp = calendar.timegm(datetime.datetime.strptime(
                        date_part, '%Y-%m-%d').timetuple()) * 1000
                if not self.dateStart <= date_timestamp <= self.dateEnd:
                    return

            self.inWay = True
            self.wayCount += 1
            self.user = attributes.get('user')
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
            if attributes.get('k') == self.tagName:
                self.found = True

        else:
            pass
            # print 'Node not known %s' % name

    def endElement(self, name):
        """Callback for when an element start is encountered.

        :param name: The name of the element that has ended.
        :type name: str
        """
        if name == 'old' and self.ignoreOld:
            self.ignoreOld = False

        if name == 'way':
            if self.found:
                # Its a target object so update it and node counts
                if self.user in self.wayCountDict:
                    value = self.wayCountDict[self.user]
                    self.wayCountDict[self.user] = value + 1
                    value = self.nodeCountDict[self.user]
                    self.nodeCountDict[self.user] = value + self.nodeCount
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
