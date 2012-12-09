import logging
import urllib2
import os
import time
import optparse
from flask import Flask, url_for, render_template, abort, Response
from xml.dom.minidom import parse
import sqlite3 as sqlite

SQLITE_CONNECTION = None
DB_PATH = os.path.join(os.path.pardir(__file__), '..', 'reporter.db')
LOGGER = logging.getLogger('osm-reporter')
# Optional list of team members
CREW_LIST = ['Jacoline', 'NicoKriek', 'Babsie']
app = Flask(__name__)

@app.route('/')
def current_status():
    myUrlPath = ('http://www.openstreetmap.org/api/0.6/'
                 'map?bbox=20.411482,-34.053726,20.467358,-34.009483')
    myFilePath = '/tmp/swellendam.osm'
    myDom = load_osm_dom(myFilePath, myUrlPath)
    mySortedUserList = osm_building_contributions(myDom)
    return render_template('base.html', mySortedUserList=mySortedUserList)


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
    myUserList = []
    for myKey, myValue in myWayCountDict.iteritems():
        myCrewFlag = False
        if myKey in CREW_LIST:
            myCrewFlag = True
        myUserList.append({'name': myKey,
                           'ways': myValue,
                           'nodes': myNodeCountDict[myKey],
                           'crew': myCrewFlag})

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


def close_connection():
    """Given an sqlite3 connection, close it.

    Args:
        None

    Returns:
        None

    Raises:
        None
    """
    if SQLITE_CONNECTION is not None:
        SQLITE_CONNECTION.close()
        SQLITE_CONNECTION = None


def open_connection():
    """Open an sqlite connection to the database.

    Args:
        thePath - path to the desired sqlite db to use.
    Returns:
        None
    Raises:
        An sqlite.Error is raised if anything goes wrong
    """
    SQLITE_CONNECTION = None
    try:
        SQLITE_CONNECTION = sqlite.connect(DB_PATH)
    except sqlite.Error, e:
        LOGGER.exception("Error opening SQLITE db : %s:" % e.args[0])
        raise


def get_cursor():
    """Get a cursor for the active SQLITE_CONNECTION. The cursor can be used to
    execute arbitrary queries against the database. This method also checks
    that the keywords table exists in the schema, and if not, it creates
    it.

    Args:
        None

    Returns:
        a valid cursor opened against the SQLITE_CONNECTION.

    Raises:
        An sqlite.Error will be raised if anything goes wrong
    """
    if SQLITE_CONNECTION is None:
        open_connection()
    try:
        myCursor = SQLITE_CONNECTION.cursor()
        myCursor.execute('SELECT SQLITE_VERSION()')
        myData = myCursor.fetchone()
        #print "SQLite version: %s" % myData
        # Check if we have some tables, if not create them
        mySQL = 'select sql from sqlite_master where type = \'table\';'
        myCursor.execute(mySQL)
        myData = myCursor.fetchone()
        #print "Tables: %s" % myData
        if myData is None:
            #print 'No tables found'
            mySQL = ('create table record (id serial not null primary key, '
                     'user varchar(255) not null,'
                     'log_date date not null,'
                     'ways int not null default 0,'
                     'nodes int not null default 0,'
                     ');')
            print mySQL
            myCursor.execute(mySQL)
            myData = myCursor.fetchone()
        else:
            #print 'Keywords table already exists'
            pass
        return myCursor
    except sqlite.Error, e:
        print "Error %s:" % e.args[0]
        raise


def write_record(theRecord):
    """Write a record to the database.

    Args:

       * theRecord: dict in the form of  { 'user': <user>, 'ways':
            <way count>, 'nodes': <node count>, 'crew': <bool> }

    Returns:
       None

    Raises:
       None
    """
    try:
        myCursor = get_cursor()
        mySQL = ('insert into record (user, log_date, ways, nodes) values ('
                 '\'%s\',\'%s\',\'%s\',\'%s\',' % (
            theRecord['user'],
            theRecord['log_date'],
            theRecord['ways'],
            theRecord['nodes']
        ))
        myCursor.execute(mySQL)
        SQLITE_CONNECTION.commit()
    except sqlite.Error, e:
        LOGGER.exception('SQLITE Error %s:' % e.args[0])
        SQLITE_CONNECTION.rollback()
    except Exception, e:
        LOGGER.exception("Error %s:" % e.args[0])
        SQLITE_CONNECTION.rollback()
        raise
    finally:
        close_connection()


def read_records(self, the_date):
    """Read all records for users given a date.

    Note that a record contains the cumulative total of data captured as
    at the query date.

    Args:
       * theDate: date for which records should be read.

    Returns:
       A list of dicts.

    Raises:
       None
    """
    open_connection()
    myList = []
    try:
        myCursor = self.getCursor()
        #now see if we have any data for our hash
        mySQL = 'select * from record where date = %s' % the_date
        myCursor.execute(mySQL)
        myRows = myCursor.fetchall()
        if len(myRows) is None:
            LOGGER.exception('No records found for %s' % the_date)
        else:
            for myRow in myRows:
                myUser = myRow[0]  # first field
                myDate = myRow[1]
                myWays = myRow[2]
                myNodes = myRow[3]
                myDict = {'user': myUser,
                          'date': myDate,
                          'ways': myWays,
                          'nodes': myNodes}
                myList.append(myDict)

    except sqlite.Error, e:
        print "Error %s:" % e.args[0]
    except Exception, e:
        print "Error %s:" % e.args[0]
        raise
    finally:
        close_connection()
    return myList

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
        app.debug = True
        # set up flask to serve static content
        app.add_url_rule('/<path:path>', 'static_file', static_file)
    app.run()
