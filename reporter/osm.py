# coding=utf-8
"""Module for low level OSM file retrieval.
:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""
import hashlib
import urllib2
import time
import os
from subprocess import call

from reporter.utilities import temp_dir, unique_filename, zip_shp, which
from reporter import config
from reporter import LOGGER


def get_osm_file(bbox, coordinates):
    """Fetch an osm file given a bounding box using the overpas API.

    Args:
        bbox: list - [min lat, min lon, max lat, max lon]
        coordinates: TODO: document this

    Returns:
        file: a file object which has been opened on the retrieved OSM dataset.

    Raises:
        None

    Note bbox is min lat, min lon, max lat, max lon

    Coordinates look like this:
    {'NE_lng': 20.444537401199337,
     'SW_lat': -34.0460012312071,
     'SW_lng': 20.439494848251343,
     'NE_lat': -34.044441058971394}

             Example overpass API query for buildings (testable at
        http://overpass-turbo.eu/)::

            (
              node
                ["building"]
                ["building"!="no"]
              ({{bbox}});
              way
                ["building"]
                ["building"!="no"]
              ({{bbox}});
              rel
                ["building"]
                ["building"!="no"]
              ({{bbox}});
            <;);out+meta;

        Equivalent url (http encoded)::



    """

    # myUrlPath = (
    #     'http://overpass-api.de/api/interpreter?'
    #     'data=('
    #     'node["building"]["building"!="no"]'
    #     '(%(SW_lat)s,%(SW_lng)s,%(NE_lat)s,%(NE_lng)s);'
    #     'way["building"]["building"!="no"]'
    #     '(%(SW_lat)s,%(SW_lng)s,%(NE_lat)s,%(NE_lng)s);'
    #     'relation["building"]["building"!="no"]'
    #     '(%(SW_lat)s,%(SW_lng)s,%(NE_lat)s,%(NE_lng)s);'
    #     '<;);out+meta;' % coordinates)
    myUrlPath = ('http://overpass-api.de/api/interpreter?data='
                 '(node({SW_lat},{SW_lng},{NE_lat},{NE_lng});<;);out+meta;'
                 .format(**coordinates))
    mySafeName = hashlib.md5(bbox).hexdigest() + '.osm'
    myFilePath = os.path.join(
        config.CACHE_DIR,
        mySafeName)
    return load_osm_document(myFilePath, myUrlPath)


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
    except urllib2.URLError:
        LOGGER.exception('Bad Url or Timeout')
        raise


def extract_buildings_shapefile(theFilePath):
    """Convert the OSM xml file to a buildings shapefile.

        This is a multistep process:
            * Create a temporary postgis database
            * Load the osm dataset into POSTGIS with osm2pgsql and our custom
                 style file.
            * Save the data out again to a shapefile
            * Zip the shapefile ready for user to download
        Args:
            theFilePath: str - path to the OSM file name.

        Returns:
            str - path to zipfile that was created.

        Raises:
            None
    """
    work_dir = temp_dir(sub_dir='buildings')
    directory_name = unique_filename(dir=work_dir)
    os.makedirs(directory_name)

    resource_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'resources'))
    style_file = os.path.join(resource_path, 'building.style')
    db_name = os.path.basename(directory_name)
    shape_path = os.path.join(directory_name, 'buildings.shp')

    createdb_exectuable = which('createdb')[0]
    createdb_command = '%s -T template_postgis %s' % (
        createdb_exectuable, db_name)

    osm2pgsql_executable = which('osm2pgsql')[0]
    osm2pgsql_command = '%s -S %s -d %s %s' % (
        osm2pgsql_executable, style_file, db_name, theFilePath)

    pgsql2shp_executable = which('pgsql2shp')[0]
    pgsql2shp_command = '%s -f %s %s planet_osm_polygon' % (
        pgsql2shp_executable, shape_path, db_name)

    dropdb_executable = which('dropdb')[0]
    dropdb_command = '%s %s' % (dropdb_executable, db_name)

    # Now run the commands in sequence:
    print createdb_command
    call(createdb_command, shell=True)
    print osm2pgsql_command
    call(osm2pgsql_command, shell=True)
    print pgsql2shp_command
    call(pgsql2shp_command, shell=True)
    print dropdb_command
    call(dropdb_command, shell=True)

    # Now zip it up and return the path to the zip, removing the original shp
    zipfile = zip_shp(shape_path, remove_file=True)
    return zipfile

