import xml
import xml.sax
import logging
import time
from datetime import date, timedelta

import config
from reporter.osm_node_parser import OsmNodeParser
from reporter.osm_way_parser import OsmParser
from reporter.logger import setup_logger

setup_logger()
LOGGER = logging.getLogger('osm-reporter')


def get_totals(sorted_user_list):
    """Given a sorted user list, get the totals for ways and nodes.

    Args:
        sorted_user_list: list - of user dicts sorted by number of ways.

    Returns:
        (int, int): two-tuple containing way count, node count.
    """
    myWayCount = 0
    myNodeCount = 0
    for myUser in sorted_user_list:
        myWayCount += myUser['ways']
        myNodeCount += myUser['nodes']
    return myNodeCount, myWayCount


def split_bbox(bbox):
    """Split a bounding box into its parts.

    Args:
        bbox: str - a string describing a bbox e.g. '106.78674459457397,
            -6.141301491467023,106.80691480636597,-6.133834354201348'

    Returns:
        dict: with keys: 'southwest_lng, southwest_lat, northeast_lng,
            northeast_lat'

    Raises:
        None
    """
    values = bbox.split(',')
    if not len(values) == 4:
        raise ValueError('Invalid bbox')
    # pylint: disable=W0141
    # next line should probably use list comprehension rather
    # http://pylint-messages.wikidot.com/messages:w0141
    values = map(float, values)
    # pylint: enable=W0141
    names = ['SW_lng', 'SW_lat', 'NE_lng', 'NE_lat']
    coordinates = dict(zip(names, values))
    return coordinates


def osm_object_contributions(osm_file, tag_name):
    """Compile a summary of user contributions for the selected osm data type.

    Args:
        osm_file: file - a file object reading from a .osm file.
        tag_name: str - the tag name we want to filter on.

    Returns:
        list: a list of dicts where items in the list are sorted from highest
            contributor (based on number of ways) down to lowest. Each element
            in the list is a dict in the form: {
            'user': <user>,
            'ways': <way count>,
            'nodes': <node count>,
            'timeline': <timelinedict>,
            'crew': <bool> }
            where crew is used to designate users who are part of an active
            data gathering campaign.
            The timeline dict will contain a collection of dates and
            the total number of ways created on that date e.g.
            {
                u'2010-12-09': 10,
                u'2012-07-10': 14
            }
    Raises:
        None
    """
    myParser = OsmParser(tagName=tag_name)
    xml.sax.parse(osm_file, myParser)
    myWayCountDict = myParser.wayCountDict
    myNodeCountDict = myParser.nodeCountDict
    myTimeLines = myParser.userDayCountDict

    # Convert to a list of dicts so we can sort it.
    myCrewList = config.CREW
    myUserList = []

    for myKey, myValue in myWayCountDict.iteritems():
        myCrewFlag = False
        if myKey in myCrewList:
            myCrewFlag = True
        myStartDate, myEndDate = date_range(myTimeLines[myKey])
        myStartDate = time.strftime('%d-%m-%Y', myStartDate.timetuple())
        myEndDate = time.strftime('%d-%m-%Y', myEndDate.timetuple())
        myRecord = {'name': myKey,
                    'ways': myValue,
                    'nodes': myNodeCountDict[myKey],
                    'timeline': interpolated_timeline(myTimeLines[myKey]),
                    'start': myStartDate,
                    'end': myEndDate,
                    'activeDays': len(myTimeLines[myKey]),
                    'crew': myCrewFlag}
        myUserList.append(myRecord)

    # Sort it
    mySortedUserList = sorted(
        myUserList, key=lambda d: (-d['ways'],
                                   d['nodes'],
                                   d['name'],
                                   d['timeline'],
                                   d['start'],
                                   d['end'],
                                   d['activeDays'],
                                   d['crew']))
    return mySortedUserList


def date_range(timeline):
    """Given a timeline, determine the start and end dates.

    The timeline may be sparse (containing fewer entries than all the dates
    between the min and max dates) and since it is a dict,
    the dates may be in any order.

    Args:
        timeline: dict - a dictionary of non-sequential dates (in
            YYYY-MM-DD) as keys and values (representing ways collected on that
            day).

    Returns:
        myStartDate - a date object representing the earliest date in the time
            line.
        myEndDate - a date object representing the newest date in the time
            line.

    Raises:
        None
    """
    myStartDate = None
    myEndDate = None
    for myDate in timeline.keys():
        myYear, myMonth, myDay = myDate.split('-')
        LOGGER.info('Date: %s' % myDate)
        myTimelineDate = date(int(myYear), int(myMonth), int(myDay))
        if myStartDate is None:
            myStartDate = myTimelineDate
        if myEndDate is None:
            myEndDate = myTimelineDate
        if myTimelineDate < myStartDate:
            myStartDate = myTimelineDate
        if myTimelineDate > myEndDate:
            myEndDate = myTimelineDate
    return myStartDate, myEndDate


def interpolated_timeline(timeline):
    """Interpolate a timeline given a sparse timeline.

    A sparse timelines is a sequence of dates containing no days of zero
    activity. An interpolated timeline is a sequence of dates where there is
    an entry per day in the date range regardless of whether there was any
    activity or not.

    Args:
        timeline: dict - a dictionary of non sequential dates (in
            YYYY-MM-DD) as keys and values (representing ways collected on that
            day).

    Returns:
        dict: An interpolated list where each date in the original
            input date is present, and all days where no total was provided
            are added to include that day.

    Given an input looking like this:
            {
                {u'2012-09-24': 1},
                {u'2012-09-21': 10},
                {u'2012-09-25': 5},
            }

    The returned list will be in the form:
            [
                [Date(2012,09,21), 10],
                [Date(2012,09,22), 0],
                [Date(2012,09,23), 0],
                [Date(2012,09,24), 1],
                [Date(2012,09,25), 5],
            ]
    """
    # Work out the earliest and latest day
    myStartDate, myEndDate = date_range(timeline)
    # Loop through them, adding an entry for each day
    myTimeline = '['
    for myDate in date_range_iterator(myStartDate, myEndDate):
        myDateString = time.strftime('%Y-%m-%d', myDate.timetuple())
        if myDateString in timeline:
            myValue = timeline[myDateString]
        else:
            myValue = 0
        if myTimeline != '[':
            myTimeline += ','
        myTimeline += '["%s",%i]' % (myDateString, myValue)
    myTimeline += ']'
    return myTimeline


def date_range_iterator(start_date, end_date):
    """Given two dates return a collection of dates between start and end.

    Args:
        * start_date: date instance representing the start date.
        * end_date: date instance representing the end date.

    Returns:
        Iteratable collection yielding dates.

    Raises:
        None
    """
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


def osm_nodes_by_user(theFile, username):
    """Obtain the nodes collected by a single user from an OSM file.

    Args:
        theFile: file - file handle to an open OSM XML document.
        username: str - name of the user for whom nodes should be collected.

    Returns:
        list: a list of nodes for the given user.

    Raises:
        None
    """
    myParser = OsmNodeParser(username)
    xml.sax.parse(theFile, myParser)
    return myParser.nodes
