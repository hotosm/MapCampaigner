# coding=utf-8
"""Helper utilities module to compute various statistics for the current AOI.
:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""
import os
import sys
import getpass
from tempfile import mkstemp
import xml
import time
from datetime import date, timedelta
import zipfile

import config
from reporter.osm_node_parser import OsmNodeParser
from reporter.osm_way_parser import OsmParser
from reporter import LOGGER


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
            'best': <most ways in a single day>,
            'worst': <least ways in single day>,
            'average': <average ways across active days>,
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
    try:
        xml.sax.parse(osm_file, myParser)
    except xml.sax.SAXParseException:
        LOGGER.exception('Failed to parse OSM xml.')
        raise

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
        user_timeline = myTimeLines[myKey]
        myRecord = {'name': myKey,
                    'ways': myValue,
                    'nodes': myNodeCountDict[myKey],
                    'timeline': interpolated_timeline(user_timeline),
                    'start': myStartDate,
                    'end': myEndDate,
                    'activeDays': len(user_timeline),
                    'best': best_active_day(user_timeline),
                    'worst': worst_active_day(user_timeline),
                    'average': average_for_active_days(user_timeline),
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
                                   d['best'],
                                   d['worst'],
                                   d['average'],
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


def average_for_active_days(timeline):
    """Compute the average activity per active day in a sparse timeline.

    Args:
        timeline: dict - a dictionary of non-sequential dates (in
            YYYY-MM-DD) as keys and values (representing ways collected on that
            day).

    Returns:
        int: number of entities captured per day rounded to the nearest int.

    Raises:
        None
    """
    myCount = 0
    mySum = 0
    for myValue in timeline.values():
        if myValue > 0:
            myCount += 1
            mySum += myValue
    myAverage = mySum / myCount
    return myAverage


def best_active_day(timeline):
    """Compute the best activity for a single active day in a sparse timeline.

    Args:
        timeline: dict - a dictionary of non-sequential dates (in
            YYYY-MM-DD) as keys and values (representing ways collected on that
            day).

    Returns:
        int: number of entities captured for the user's best day.

    Raises:
        None
    """
    myBest = 0
    for myValue in timeline.values():
        if myValue > myBest:
            myBest = myValue
    return myBest


def worst_active_day(timeline):
    """Compute the worst activity for a single active day in a sparse timeline.

    Args:
        timeline: dict - a dictionary of non-sequential dates (in
            YYYY-MM-DD) as keys and values (representing ways collected on that
            day).

    Returns:
        int: number of entities captured for the user's worst day.

    Raises:
        None
    """
    if len(timeline) < 1:
        return 0
    myWorst = timeline.values()[0]
    for myValue in timeline.values():
        if myValue == 0:  # should never be but just in case
            continue
        if myValue < myWorst:
            myWorst = myValue
    return myWorst


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


def temp_dir(sub_dir='work'):
    """Obtain the temporary working directory for the operating system.

    An osm-reporter subdirectory will automatically be created under this.

    .. note:: You can use this together with unique_filename to create
       a file in a temporary directory under the inasafe workspace. e.g.

       tmpdir = temp_dir('testing')
       tmpfile = unique_filename(dir=tmpdir)
       print tmpfile
       /tmp/osm-reporter/23-08-2012/timlinux/testing/tmpMRpF_C

    If you specify OSM_REPORTER_WORK_DIR as an environment var, it will be
    used in preference to the system temp directory.

    .. note:: This function was taken from InaSAFE (http://inasafe.org) with
    minor adaptions.

    Args:
        sub_dir str - optional argument which will cause an additional
                subirectory to be created e.g. /tmp/inasafe/foo/

    Returns:
        Path to the output clipped layer (placed in the system temp dir).

    Raises:
       Any errors from the underlying system calls.
    """
    user = getpass.getuser().replace(' ', '_')
    current_date = date.today()
    date_string = current_date.isoformat()
    if 'OSM_REPORTER_WORK_DIR' in os.environ:
        new_directory = os.environ['OSM_REPORTER_WORK_DIR']
    else:
        # Following 4 lines are a workaround for tempfile.tempdir()
        # unreliabilty
        handle, filename = mkstemp()
        os.close(handle)
        new_directory = os.path.dirname(filename)
        os.remove(filename)

    path = os.path.join(
        new_directory, 'osm-reporter', date_string, user, sub_dir)

    if not os.path.exists(path):
        # Ensure that the dir is world writable
        # Umask sets the new mask and returns the old
        old_mask = os.umask(0000)
        os.makedirs(path, 0777)
        # Reinstate the old mask for tmp
        os.umask(old_mask)
    return path


def unique_filename(**kwargs):
    """Create new filename guaranteed not to exist previously


    .. note:: This function was taken from InaSAFE (http://inasafe.org) with
    minor adaptions.

    Use mkstemp to create the file, then remove it and return the name

    If dir is specified, the tempfile will be created in the path specified
    otherwise the file will be created in a directory following this scheme:

    :file:`/tmp/osm-reporter/<dd-mm-yyyy>/<user>/impacts'

    See http://docs.python.org/library/tempfile.html for details.

    Example usage:

    tempdir = temp_dir(sub_dir='test')
    filename = unique_filename(suffix='.keywords', dir=tempdir)
    print filename
    /tmp/osm-reporter/23-08-2012/timlinux/test/tmpyeO5VR.keywords

    Or with no preferred subdir, a default subdir of 'impacts' is used:

    filename = unique_filename(suffix='.shp')
    print filename
    /tmp/osm-reporter/23-08-2012/timlinux/impacts/tmpoOAmOi.shp

    """

    if 'dir' not in kwargs:
        path = temp_dir('impacts')
        kwargs['dir'] = path
    else:
        path = temp_dir(kwargs['dir'])
        kwargs['dir'] = path
    if not os.path.exists(kwargs['dir']):
        # Ensure that the dir mask won't conflict with the mode
        # Umask sets the new mask and returns the old
        umask = os.umask(0000)
        # Ensure that the dir is world writable by explictly setting mode
        os.makedirs(kwargs['dir'], 0777)
        # Reinstate the old mask for tmp dir
        os.umask(umask)
        # Now we have the working dir set up go on and return the filename
    handle, filename = mkstemp(**kwargs)

    # Need to close it using the filehandle first for windows!
    os.close(handle)
    try:
        os.remove(filename)
    except OSError:
        pass
    return filename


def zip_shp(shp_path, extra_ext=None, remove_file=False):
    """Zip shape file and its gang (.shx, .dbf, .prj).

    .. note:: This function was taken from InaSAFE (http://inasafe.org) with
    minor adaptions.

    Args:
        * shp_path: str - path to the main shape file.
        * extra_ext: [str] - list of extra extensions related to shapefile.
        * remove_file: bool - whether the original shp files should be
            removed after zipping is complete. Defaults to False.
    Returns:
        str: full path to the created shapefile

    Raises:
        None

    """

    # go to the directory
    my_cwd = os.getcwd()
    shp_dir, shp_name = os.path.split(shp_path)
    os.chdir(shp_dir)

    shp_base_name, _ = os.path.splitext(shp_name)
    extensions = ['.shp', '.shx', '.dbf', '.prj']
    if extra_ext is not None:
        extensions.extend(extra_ext)

    # zip files
    zip_filename = shp_base_name + '.zip'
    zip_object = zipfile.ZipFile(zip_filename, 'w')
    for ext in extensions:
        if os.path.isfile(shp_base_name + ext):
            zip_object.write(shp_base_name + ext)
    zip_object.close()

    if remove_file:
        for ext in extensions:
            if os.path.isfile(shp_base_name + ext):
                os.remove(shp_base_name + ext)

    os.chdir(my_cwd)
    return os.path.join(shp_dir, zip_filename)


def which(name, flags=os.X_OK):
    """Search PATH for executable files with the given name.

    ..note:: This function was taken verbatim from the twisted framework,
      licence available here:
      http://twistedmatrix.com/trac/browser/tags/releases/twisted-8.2.0/LICENSE

    On newer versions of MS-Windows, the PATHEXT environment variable will be
    set to the list of file extensions for files considered executable. This
    will normally include things like ".EXE". This fuction will also find files
    with the given name ending with any of these extensions.

    On MS-Windows the only flag that has any meaning is os.F_OK. Any other
    flags will be ignored.

    @type name: C{str}
    @param name: The name for which to search.

    @type flags: C{int}
    @param flags: Arguments to L{os.access}.

    @rtype: C{list}
    @param: A list of the full paths to files found, in the
    order in which they were found.
    """
    result = []
    #pylint: disable=W0141
    exts = filter(None, os.environ.get('PATHEXT', '').split(os.pathsep))
    #pylint: enable=W0141
    path = os.environ.get('PATH', None)
    # In c6c9b26 we removed this hard coding for issue #529 but I am
    # adding it back here in case the user's path does not include the
    # gdal binary dir on OSX but it is actually there. (TS)
    if sys.platform == 'darwin':  # Mac OS X
        myGdalPrefix = ('/Library/Frameworks/GDAL.framework/'
                        'Versions/1.9/Programs/')
        path = '%s:%s' % (path, myGdalPrefix)

    LOGGER.debug('Search path: %s' % path)

    if path is None:
        return []

    for p in path.split(os.pathsep):
        p = os.path.join(p, name)
        if os.access(p, flags):
            result.append(p)
        for e in exts:
            pext = p + e
            if os.access(pext, flags):
                result.append(pext)

    return result
