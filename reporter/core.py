import os
import urllib2
import time
import optparse
import hashlib
import xml.sax

import logging
import logging.handlers

from flask import Flask, request, render_template, abort, Response

import config
from osm_parser import OsmParser

DB_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    os.path.pardir,
    'reporter.db'
)
LOGGER = logging.getLogger('osm-reporter')

app = Flask(__name__)


@app.route('/')
def current_status():
    mySortedUserList = []
    bbox = request.args.get('bbox', config.BBOX)
    try:
        coordinates = split_bbox(bbox)
    except ValueError:
        error = "Invalid bbox"
        coordinates = split_bbox(config.BBOX)
    else:
        # Note bbox is min lat, min lon, max lat, max lon
        myUrlPath = ('http://overpass-api.de/api/interpreter?data='
        '(node({SW_lat},{SW_lng},{NE_lat},{NE_lng});<;);out+meta;'.format(
            **coordinates))
        safe_name = hashlib.md5(bbox).hexdigest() + '.osm'
        myFilePath = os.path.join(
            config.CACHE_DIR,
            safe_name
        )
        try:
            myFile = load_osm_document(myFilePath, myUrlPath)
        except urllib2.URLError:
            error = "Bad request. Maybe the bbox is too big!"
        else:
            mySortedUserList = osm_building_contributions(myFile)
            error = None

    myNodeCount, myWayCount = get_totals(mySortedUserList)

    # We need to manually cast float in string, otherwise floats are
    # truncated, and then rounds in Leaflet result in a wrong bbox
    # Note: slit_bbox should better keep returning real floats
    coordinates = dict((k, repr(v)) for k, v in coordinates.iteritems())

    context = dict(
        mySortedUserList=mySortedUserList,
        myWayCount=myWayCount,
        myNodeCount=myNodeCount,
        myUserCount=len(mySortedUserList),
        bbox=bbox,
        error=error,
        coordinates=coordinates,
        display_update_control=1 if config.DISPLAY_UPDATE_CONTROL else 0,
    )
    return render_template('base.html', **context)


def get_totals(theSortedUserList):
    """Given a sorted user list, get the totals for ways and nodes.

    Args:
        theSortedUserList: list - of user dicts sorted by number of ways.

    Returns:
        (int, int): two-tuple containing waycount, node count.
    """
    myWayCount = 0
    myNodeCount = 0
    for myUser in theSortedUserList:
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
    values = map(float, values)
    names = ['SW_lng', 'SW_lat', 'NE_lng', 'NE_lat']
    coordinates = dict(zip(names, values))
    return coordinates


def load_osm_document(theFilePath, theUrlPath):
    """Load an osm document, refreshing it if the cached copy is stale.

    To save bandwidth the file is not downloaded if it is less than 1 hour old.

     Args:
        * theUrlPath - (Mandatory) The path (relative to the ftp root)
          from which the file should be retrieved.
        * theFilePath - (Mandatory). The path on the filesystem to which
          the file should be saved.
     Returns:
         file object for the the downloaded file.

     Raises:
         None
    """
    myElapsedSeconds = 0
    if os.path.exists(theFilePath):
        myTime = time.time()  # in unix epoch
        myFileTime = os.path.getmtime(theFilePath)  # in unix epoch
        myElapsedSeconds = myTime - myFileTime
        if myElapsedSeconds > 3600:
            os.remove(theFilePath)
    if myElapsedSeconds > 3600 or not os.path.exists(theFilePath):
        fetch_osm(theUrlPath, theFilePath)
        LOGGER.info('fetched %s' % theFilePath)
    myFile = open(theFilePath, 'rt')
    return myFile


def osm_building_contributions(theFile):
    """Compile a summary of user contributions for buildings.

    Args:
        theFile: a file object reading from a .osm file.

    Returns:
        list: a list of dicts where items in the list are sorted from highest
            contributor (based on number of ways) down to lowest. Each element
            in the list is a dict in the form: { 'user': <user>, 'ways':
            <way count>, 'nodes': <node count>, 'crew': <bool> } where crew
            is used to designate users who are part of an active data gathering
            campaign.
    Raises:
        None
    """
    myParser = OsmParser()
    xml.sax.parse(theFile, myParser)
    myWayCountDict = myParser.wayCountDict
    myNodeCountDict = myParser.nodeCountDict

    # Convert to a list of dicts so we can sort it.
    myCrewList = config.CREW
    myUserList = []

    for myKey, myValue in myWayCountDict.iteritems():
        myCrewFlag = False
        if myKey in myCrewList:
            myCrewFlag = True
        myRecord = {'name': myKey,
                    'ways': myValue,
                    'nodes': myNodeCountDict[myKey],
                    'crew': myCrewFlag}
        myUserList.append(myRecord)

    # Sort it
    mySortedUserList = sorted(
        myUserList, key=lambda d: (-d['ways'],
                                   d['nodes'],
                                   d['name'],
                                   d['crew']))
    return mySortedUserList


def fetch_osm(theUrlPath, theFilePath):
    """Fetch an osm map and store locally.

     Args:
        * theUrlPath - (Mandatory) The path (relative to the ftp root)
          from which the file should be retrieved.
        * theFilePath - (Mandatory). The path on the filesystem to which
          the file should be saved.

     Returns:
         The path to the downloaded file.

     Raises:
         None
    """
    LOGGER.debug('Getting URL: %s', theUrlPath)
    myRequest = urllib2.Request(theUrlPath)
    try:
        myUrlHandle = urllib2.urlopen(myRequest, timeout=60)
        myFile = file(theFilePath, 'wb')
        myFile.write(myUrlHandle.read())
        myFile.close()
    except urllib2.URLError, e:
        LOGGER.exception('Bad Url or Timeout')
        raise


def addLoggingHanderOnce(theLogger, theHandler):
    """A helper to add a handler to a logger, ensuring there are no duplicates.

    Args:
        * theLogger: logging.logger instance
        * theHandler: logging.Handler instance to be added. It will not be
            added if an instance of that Handler subclass already exists.

    Returns:
        bool: True if the logging handler was added

    Raises:
        None
    """
    myClassName = theHandler.__class__.__name__
    for myHandler in theLogger.handlers:
        if myHandler.__class__.__name__ == myClassName:
            return False

    theLogger.addHandler(theHandler)
    return True


def setupLogger():
    """Set up our logger.

    Args: None

    Returns: None

    Raises: None
    """
    myLogger = logging.getLogger('osm-reporter')
    myLogger.setLevel(logging.DEBUG)
    myDefaultHanderLevel = logging.DEBUG
    # create formatter that will be added to the handlers
    myFormatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    myTempDir = ('/tmp')
    myFilename = os.path.join(myTempDir, 'reporter.log')
    myFileHandler = logging.FileHandler(myFilename)
    myFileHandler.setLevel(myDefaultHanderLevel)
    # create console handler with a higher log level
    myConsoleHandler = logging.StreamHandler()
    myConsoleHandler.setLevel(logging.ERROR)

    try:
        #pylint: disable=F0401
        from raven.handlers.logging import SentryHandler
        from raven import Client
        #pylint: enable=F0401
        myClient = Client('http://12ef42a1d4394255a2041ac0428e8ef7:'
            '755880e336f54892bc2a65d308019997@sentry.linfiniti.com/6')
        mySentryHandler = SentryHandler(myClient)
        mySentryHandler.setFormatter(myFormatter)
        mySentryHandler.setLevel(logging.ERROR)
        addLoggingHanderOnce(myLogger, mySentryHandler)
        myLogger.debug('Sentry logging enabled')

    except:
        myLogger.debug('Sentry logging disabled. Try pip install raven')



    #Set formatters
    myFileHandler.setFormatter(myFormatter)
    myConsoleHandler.setFormatter(myFormatter)

    # add the handlers to the logger
    addLoggingHanderOnce(myLogger, myFileHandler)
    addLoggingHanderOnce(myLogger, myConsoleHandler)

#
# These are only used to serve static files when testing
#
file_suffix_to_mimetype = {
    '.css': 'text/css',
    '.jpg': 'image/jpeg',
    '.html': 'text/html',
    '.ico': 'image/x-icon',
    '.png': 'image/png',
    '.js': 'application/javascript'
}


def static_file(path):
    try:
        f = open(path)
    except IOError, e:
        abort(404)
        return
    root, ext = os.path.splitext(path)
    if ext in file_suffix_to_mimetype:
        return Response(f.read(), mimetype=file_suffix_to_mimetype[ext])
    return f.read()


if __name__ == '__main__':
    setupLogger()
    parser = optparse.OptionParser()
    parser.add_option('-d', '--debug', dest='debug', default=False,
                      help='turn on Flask debugging', action='store_true')

    options, args = parser.parse_args()

    if options.debug:
        LOGGER.info('Running in debug mode')
        app.debug = True
        # set up flask to serve static content
        app.add_url_rule('/<path:path>', 'static_file', static_file)
    else:
        LOGGER.info('Running in production mode')
    app.run()
