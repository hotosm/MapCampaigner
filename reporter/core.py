import logging
import urllib2
import os
import time
import optparse
from xml.dom.minidom import parse
import hashlib

from flask import Flask, request, render_template, abort, Response

from reporter import config

DB_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    os.path.pardir,
    'reporter.db'
)
LOGGER = logging.getLogger('osm-reporter')
# Optional list of team members
CREW_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    os.path.pardir,
    'crew.txt'
)

app = Flask(__name__)


@app.route('/')
def current_status():
    error = None
    mySortedUserList = []
    bbox = request.args.get('bbox', config.BBOX)
    try:
        coordinates = split_bbox(bbox)
    except ValueError:
        error = "Invalid bbox"
        coordinates = split_bbox(config.BBOX)
    else:
        myUrlPath = ('http://www.openstreetmap.org/api/0.6/'
                     'map?bbox=%s' % bbox)
        safe_name = hashlib.md5(bbox).hexdigest()
        myFilePath = os.path.join(
            '/tmp',
            'reporter',
            safe_name
        )
        try:
            myDom = load_osm_dom(myFilePath, myUrlPath)
        except urllib2.URLError:
            error = "Bad request. Maybe the bbox is too big!"
        else:
            mySortedUserList = osm_building_contributions(myDom)
            error = None
    context = dict(
        mySortedUserList=mySortedUserList,
        bbox=bbox,
        error=error,
        coordinates=coordinates
    )
    return render_template('base.html', **context)


def split_bbox(bbox):
    """
    Return a dict with 'southwest_lng,southwest_lat,northeast_lng,northeast_lat'
    keys from a bbox string.
    """
    values = bbox.split(',')
    if not len(values) == 4:
        raise ValueError('Invalid bbox')
    values = map(float, values)
    names = ['SW_lng', 'SW_lat', 'NE_lng', 'NE_lat']
    coordinates = dict(zip(names, values))
    return coordinates


def crew_list():
    """Get a list of 'crew' - people involved in your project.

    Args:
        None

    Returns:
        list: list of str where each is a crew member name. If not crew
            file exists or members are defined, an empty list is returned.

    Raises:
        None

    Example::

        myList = crew_list()
        print str(myList)
        ['timlinux', 'foo', 'bar']
    """
    if os.path.exists(CREW_PATH):
        with open(CREW_PATH, 'r') as myFile:
            myLines = myFile.read().splitlines()
        return myLines
    else:
        return []


def load_osm_dom(theFilePath, theUrlPath):
    """Load an osm document, refreshing it if the cached copy is stale.

    To save bandwidth the file is not downloaded if it is less than 1 hour old.

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
    myDom = parse(myFile)
    myFile.close()
    return myDom


def osm_building_contributions(theDom):
    """Compile a summary of user contributions for buildings.

    Args:
        theDom: a minidom document as read from a .osm file.

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
    myWayCountDict = {}
    myNodeCountDict = {}
    myWays = theDom.getElementsByTagName('way')
    for myWay in myWays:
        if myWay.hasAttribute('user'):
            myUser = myWay.attributes['user'].value
            myNodes = myWay.getElementsByTagName('nd')

            # See if we have a building way
            myBuildingFlag = False
            myTags = myWay.getElementsByTagName('tag')
            for myTag in myTags:
                for myValue in myTag.attributes.values():
                    if 'building' == myValue.value:
                        myBuildingFlag = True
            if not myBuildingFlag:
                continue

            # Its a building so update our building and node counts
            if myUser in myWayCountDict:
                myValue = myWayCountDict[myUser]
                myWayCountDict[myUser] = myValue + 1
                myValue = myNodeCountDict[myUser]
                if myNodes:
                    myNodeCountDict[myUser] = myValue + len(myNodes)
            else:
                myWayCountDict[myUser] = 1
                if myNodes:
                    myNodeCountDict[myUser] = len(myNodes)

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
