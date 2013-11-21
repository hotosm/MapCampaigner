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
from shutil import copyfile

from .utilities import temp_dir, unique_filename, zip_shp, which
from . import config
from . import LOGGER


def get_osm_file(bbox, coordinates):
    """Fetch an osm file given a bounding box using the overpass API.

    .. todo:: Refactor so that we don't need to pass the same param twice in
        different forms!

    :param bbox: Coordinates as a string
        as passed in via the http request object.
    :type bbox: str

    :param coordinates: Coordinates as a list in the form:
        [min lat, min lon, max lat, max lon]

    :returns: A file which has been opened on the retrieved OSM dataset.
    :rtype: file

    .. note:: bbox is min lat, min lon, max lat, max lon

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
    # This is my preferred way to query overpass since it only fetches back
    # building features (we would adapt it to something similar for roads)
    # so it is much more efficient. However it (the retrieved osm xml
    # file) works for the report but not for the shp2pgsql stuff lower down.
    # So for now it is commented out. Tim.
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
    # Overpass query to fetch all features in extent
    myUrlPath = ('http://overpass-api.de/api/interpreter?data='
                 '(node({SW_lat},{SW_lng},{NE_lat},{NE_lng});<;);out+meta;'
                 .format(**coordinates))
    mySafeName = hashlib.md5(bbox).hexdigest() + '.osm'
    myFilePath = os.path.join(config.CACHE_DIR, mySafeName)
    return load_osm_document(myFilePath, myUrlPath)


def load_osm_document(file_path, url_path):
    """Load an osm document, refreshing it if the cached copy is stale.

    To save bandwidth the file is not downloaded if it is less than 1 hour old.

    :param url_path: Path (relative to the ftp root) from which the file
        should be retrieved.
    :type url_path: str

    :param file_path: The path on the filesystem to which the file should
        be saved.
    :type file_path: str

    :returns: A file object for the the downloaded file.
    :rtype: file

     Raises:
         None
    """
    myElapsedSeconds = 0
    if os.path.exists(file_path):
        myTime = time.time()  # in unix epoch
        myFileTime = os.path.getmtime(file_path)  # in unix epoch
        myElapsedSeconds = myTime - myFileTime
        if myElapsedSeconds > 3600:
            os.remove(file_path)
    if myElapsedSeconds > 3600 or not os.path.exists(file_path):
        fetch_osm(file_path, url_path)
        myMessage = ('fetched %s' % file_path)
        LOGGER.info(myMessage)
    myFile = open(file_path, 'rt')
    return myFile


def fetch_osm(file_path, url_path):
    """Fetch an osm map and store locally.


    :param url_path: The path (relative to the ftp root) from which the
        file should be retrieved.
    :type url_path: str

    :param file_path: The path on the filesystem to which the file should
        be saved.
    :type file_path: str

    :returns: The path to the downloaded file.

    """
    LOGGER.debug('Getting URL: %s', url_path)
    myRequest = urllib2.Request(url_path)
    try:
        myUrlHandle = urllib2.urlopen(myRequest, timeout=60)
        myFile = file(file_path, 'wb')
        myFile.write(myUrlHandle.read())
        myFile.close()
    except urllib2.URLError:
        LOGGER.exception('Bad Url or Timeout')
        raise


def extract_buildings_shapefile(file_path):
    """Convert the OSM xml file to a buildings shapefile.

        This is a multistep process:
            * Create a temporary postgis database
            * Load the osm dataset into POSTGIS with osm2pgsql and our custom
                 style file.
            * Save the data out again to a shapefile
            * Zip the shapefile ready for user to download

        :param file_path: Path to the OSM file name.
        :type file_path: str

        :returns: Path to zipfile that was created.
        :rtype: str

    """
    work_dir = temp_dir(sub_dir='buildings')
    directory_name = unique_filename(dir=work_dir)
    os.makedirs(directory_name)

    resource_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'resources', 'buildings'))
    style_file = os.path.join(resource_path, 'buildings.style')
    db_name = os.path.basename(directory_name)
    shape_path = os.path.join(directory_name, 'buildings.shp')
    qml_source_path = os.path.join(resource_path, 'buildings.qml')
    qml_dest_path = os.path.join(directory_name, 'buildings.qml')
    keywords_source_path = os.path.join(resource_path, 'buildings.keywords')
    keywords_dest_path = os.path.join(directory_name, 'buildings.keywords')
    license_source_path = os.path.join(resource_path, 'buildings.license')
    license_dest_path = os.path.join(directory_name, 'buildings.license')
    prj_source_path = os.path.join(resource_path, 'buildings.prj')
    prj_dest_path = os.path.join(directory_name, 'buildings.prj')
    transform_path = os.path.join(resource_path, 'transform.sql')

    export_query = (
        '"SELECT st_transform(way, 4326) AS the_geom, '
        'building AS building, '
        '\\"building:structure\\" AS structure, '
        '\\"building:walls\\" AS wall_type, '
        '\\"building:roof\\" AS roof_type, '
        '\\"building:levels\\" AS levels, '
        'admin_level AS admin, '
        '\\"access:roof\\" AS roof_access, '
        '\\"capacity:persons\\" AS capacity, '
        'religion, '
        '\\"type:id\\" AS osm_type , '
        '\\"addr:full\\" AS full_address, '
        'name, '
        'amenity, '
        'leisure, '
        '\\"building:use\\" AS use, '
        'office, '
        'type '
        'FROM planet_osm_polygon '
        'WHERE building != \'no\';"')

    createdb_exectuable = which('createdb')[0]
    createdb_command = '%s -T template_postgis %s' % (
        createdb_exectuable, db_name)

    osm2pgsql_executable = which('osm2pgsql')[0]
    osm2pgsql_command = '%s -S %s -d %s %s' % (
        osm2pgsql_executable, style_file, db_name, file_path)

    psql_executable = which('psql')[0]
    transform_command = '%s %s -f %s' % (
        psql_executable, db_name, transform_path)

    pgsql2shp_executable = which('pgsql2shp')[0]
    pgsql2shp_command = '%s -f %s %s %s' % (
        pgsql2shp_executable, shape_path, db_name, export_query)

    dropdb_executable = which('dropdb')[0]
    dropdb_command = '%s %s' % (dropdb_executable, db_name)

    # Now run the commands in sequence:
    print createdb_command
    call(createdb_command, shell=True)
    print osm2pgsql_command
    call(osm2pgsql_command, shell=True)
    print transform_command
    call(transform_command, shell=True)
    print pgsql2shp_command
    call(pgsql2shp_command, shell=True)
    print dropdb_command
    call(dropdb_command, shell=True)

    copyfile(prj_source_path, prj_dest_path)
    copyfile(qml_source_path, qml_dest_path)
    copyfile(keywords_source_path, keywords_dest_path)
    copyfile(license_source_path, license_dest_path)

    # Now zip it up and return the path to the zip, removing the original shp
    zipfile = zip_shp(shape_path, extra_ext=[
        '.qml', '.keywords', '.license'], remove_file=True)
    return zipfile


def extract_roads_shapefile(file_path):
    """Convert the OSM xml file to a roads shapefile.

        This is a multistep process:
            * Create a temporary postgis database
            * Load the osm dataset into POSTGIS with osm2pgsql and our custom
                 style file.
            * Save the data out again to a shapefile
            * Zip the shapefile ready for user to download

        :param file_path: Path to the OSM file name.
        :type file_path: str

        :returns: Path to zipfile that was created.
        :rtype: str

    """
    work_dir = temp_dir(sub_dir='roads')
    directory_name = unique_filename(dir=work_dir)
    os.makedirs(directory_name)

    resource_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'resources', 'roads'))
    style_file = os.path.join(resource_path, 'roads.style')
    db_name = os.path.basename(directory_name)
    shape_path = os.path.join(directory_name, 'roads.shp')
    qml_source_path = os.path.join(resource_path, 'roads.qml')
    qml_dest_path = os.path.join(directory_name, 'roads.qml')
    keywords_source_path = os.path.join(resource_path, 'roads.keywords')
    keywords_dest_path = os.path.join(directory_name, 'roads.keywords')
    license_source_path = os.path.join(resource_path, 'roads.license')
    license_dest_path = os.path.join(directory_name, 'roads.license')
    prj_source_path = os.path.join(resource_path, 'roads.prj')
    prj_dest_path = os.path.join(directory_name, 'roads.prj')
    transform_path = os.path.join(resource_path, 'transform.sql')

    export_query = (
        '"SELECT st_transform(way, 4326) AS the_geom, '
        '"name", highway as type '
        'FROM planet_osm_line '
        'WHERE highway != \'no\';"')

    createdb_exectuable = which('createdb')[0]
    createdb_command = '%s -T template_postgis %s' % (
        createdb_exectuable, db_name)

    osm2pgsql_executable = which('osm2pgsql')[0]
    osm2pgsql_command = '%s -S %s -d %s %s' % (
        osm2pgsql_executable, style_file, db_name, file_path)

    psql_executable = which('psql')[0]
    transform_command = '%s %s -f %s' % (
        psql_executable, db_name, transform_path)

    pgsql2shp_executable = which('pgsql2shp')[0]
    pgsql2shp_command = '%s -f %s %s %s' % (
        pgsql2shp_executable, shape_path, db_name, export_query)

    dropdb_executable = which('dropdb')[0]
    dropdb_command = '%s %s' % (dropdb_executable, db_name)

    # Now run the commands in sequence:
    print createdb_command
    call(createdb_command, shell=True)
    print osm2pgsql_command
    call(osm2pgsql_command, shell=True)
    print transform_command
    call(transform_command, shell=True)
    print pgsql2shp_command
    call(pgsql2shp_command, shell=True)
    print dropdb_command
    call(dropdb_command, shell=True)

    copyfile(prj_source_path, prj_dest_path)
    copyfile(qml_source_path, qml_dest_path)
    copyfile(keywords_source_path, keywords_dest_path)
    copyfile(license_source_path, license_dest_path)

    # Now zip it up and return the path to the zip, removing the original shp
    zipfile = zip_shp(shape_path, extra_ext=[
        '.qml', '.keywords', '.license'], remove_file=True)
    print 'Shape written to %s' % shape_path
    return zipfile
