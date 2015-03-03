# coding=utf-8
"""Module for low level OSM file retrieval.
:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""
import hashlib
import urllib2
import time
import os
import re
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
    # url_path = (
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
    url_path = (
        'http://overpass-api.de/api/interpreter?data='
        '(node({SW_lat},{SW_lng},{NE_lat},{NE_lng});<;);out+meta;'
        .format(**coordinates))
    safe_name = hashlib.md5(bbox).hexdigest() + '.osm'
    file_path = os.path.join(config.CACHE_DIR, safe_name)
    return load_osm_document(file_path, url_path)


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
    elapsed_seconds = 0
    if os.path.exists(file_path):
        current_time = time.time()  # in unix epoch
        file_time = os.path.getmtime(file_path)  # in unix epoch
        elapsed_seconds = current_time - file_time
        if elapsed_seconds > 3600:
            os.remove(file_path)
    if elapsed_seconds > 3600 or not os.path.exists(file_path):
        fetch_osm(file_path, url_path)
        message = ('fetched %s' % file_path)
        LOGGER.info(message)
    file_handle = open(file_path, 'rb')
    return file_handle


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
    request = urllib2.Request(url_path)
    try:
        url_handle = urllib2.urlopen(request, timeout=60)
        file_handle = file(file_path, 'wb')
        file_handle.write(url_handle.read())
        file_handle.close()
    except urllib2.URLError:
        LOGGER.exception('Bad Url or Timeout')
        raise


def add_keyword_timestamp(keywords_file_path):
    """Add the current date / time to the keywords file.

    :param keywords_file_path: Keywords file path that the timestamp should be
        written to.
    :type keywords_file_path: str
    """
    time_stamp = time.strftime('%d-%m-%Y %H:%M')
    keywords_file = file(keywords_file_path, 'ab')
    keywords_file.write('date: %s' % time_stamp)
    keywords_file.close()


def extract_buildings_shapefile(
        file_path, qgis_version=2, output_prefix=''):
    """Convert the OSM xml file to a buildings shapefile.

    This is a multistep process:
        * Create a temporary postgis database
        * Load the osm dataset into POSTGIS with osm2pgsql and our custom
             style file.
        * Save the data out again to a shapefile
        * Zip the shapefile ready for user to download

    :param file_path: Path to the OSM file name.
    :type file_path: str

    :param qgis_version: Get the QGIS version. Currently 1,
        2 are accepted, default to 2. A different qml style file will be
        returned depending on the version
    :type qgis_version: int

    :param output_prefix: Base name for the shape file. Defaults to ''
        which will result in an output file of 'buildings.shp'. Adding a
        prefix of e.g. 'test-' would result in a downloaded file name of
        'test-buildings.shp'. Allowed characters are [a-zA-Z-_0-9].
    :type output_prefix: str

    :returns: Path to zipfile that was created.
    :rtype: str

    """
    if not check_string(output_prefix):
        error = 'Invalid output prefix: %s' % output_prefix
        LOGGER.exception(error)
        raise Exception(error)

    feature_type = 'buildings'
    output_prefix += feature_type

    # Used to extract the buildings as a shapefile from pg
    # We don't store in an sql file as the sql needs to be escaped
    # as it is passed as an inline command line option to pgsql2shp
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

    return perform_extract(
        export_query,
        feature_type,
        file_path,
        output_prefix,
        qgis_version)


def extract_buildings_points_shapefile(file_path, qgis_version=2, output_prefix=''):
    """Convert the OSM xml file to a buildings points shapefile.

    This is a multistep process:
        * Create a temporary postgis database
        * Load the osm dataset into POSTGIS with osm2pgsql and our custom
             style file.
        * Save the data out again to a shapefile
        * Zip the shapefile ready for user to download

    :param file_path: Path to the OSM file name.
    :type file_path: str

    :param qgis_version: Get the QGIS version. Currently 1,
        2 are accepted, default to 2. A different qml style file will be
        returned depending on the version
    :type qgis_version: int

    :param output_prefix: Base name for the shape file. Defaults to ''
        which will result in an output file of 'buildings.shp'. Adding a
        prefix of e.g. 'test-' would result in a downloaded file name of
        'test-buildings.shp'. Allowed characters are [a-zA-Z-_0-9].
    :type output_prefix: str

    :returns: Path to zipfile that was created.
    :rtype: str

    """
    if not check_string(output_prefix):
        error = 'Invalid output prefix: %s' % output_prefix
        LOGGER.exception(error)
        raise Exception(error)

    feature_type = 'buildings-points'
    output_prefix += feature_type

    # Used to extract the buildings as a shapefile from pg
    # We don't store in an sql file as the sql needs to be escaped
    # as it is passed as an inline command line option to pgsql2shp
    export_query = (
        '"SELECT st_transform(st_pointonsurface(way), 4326) AS the_geom, '
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

    return perform_extract(
        export_query,
        feature_type,
        file_path,
        output_prefix,
        qgis_version)


def extract_roads_shapefile(file_path, qgis_version=2, output_prefix=''):
    """Convert the OSM xml file to a roads shapefile.

    .. note:: I know it is misleading, but osm2pgsql puts the roads into
        planet_osm_line table not planet_osm_roads !

    This is a multistep process:
        * Create a temporary postgis database
        * Load the osm dataset into POSTGIS with osm2pgsql and our custom
             style file.
        * Save the data out again to a shapefile
        * Zip the shapefile ready for user to download

    :param file_path: Path to the OSM file name.
    :type file_path: str

    :param qgis_version: Get the QGIS version. Currently 1,
        2 are accepted, default to 1. A different qml style file will be
        returned depending on the version
    :type qgis_version: int

    :param output_prefix: Base name for the shape file. Defaults to 'roads'
        which will result in an output file of 'roads.shp'.  Adding a
        prefix of e.g. 'test-' would result in a downloaded file name of
        'test-roads.shp'. Allowed characters are [a-zA-Z-_0-9].
    :type output_prefix: str

    :returns: Path to zipfile that was created.
    :rtype: str

    """
    if not check_string(output_prefix):
        error = 'Invalid output prefix: %s' % output_prefix
        LOGGER.exception(error)
        raise Exception(error)
    feature_type = 'roads'
    output_prefix += feature_type
    # Used to extract the roads as a shapefile from pg
    # We don't store in an sql file as the sql needs to be escaped
    # as it is passed as an inline command line option to pgsql2shp
    export_query = (
        '"SELECT st_transform(way, 4326) AS the_geom, '
        '"name", '
        'highway as osm_type,'
        'type '
        'FROM planet_osm_line '
        'WHERE highway != \'no\';"')

    return perform_extract(
        export_query,
        feature_type,
        file_path,
        output_prefix,
        qgis_version)


def check_string(text, search=re.compile(r'[^A-Za-z0-9-_]').search):
    """Test that a string doesnt contain unwanted characters.

    :param text: Text that you want to verify is compliant.
    :type text: str

    :param search: Regex to use to check the string. Defaults to allowing
        [^a-z0-9-_].

    :return: bool
    """
    return not bool(search(text))


def perform_extract(
        export_query,
        feature_type,
        file_path,
        output_prefix,
        qgis_version):
    """
    Generic method to perform an extract for a feature type.

    :param export_query: A suitable query for extracting data from the OSM
        file which has been loaded into postgresql. See one of the calling
        functions for an example of this.
    :type export_query: str

    :param feature_type: The type of feature to extract. Currently 'roads' and
        'buildings' are supported - more to be added in the future.
    :type feature_type: str

    :param file_path: Path to the OSM file name.
    :type file_path: str

    :param qgis_version: Get the QGIS version. Currently 1,
        2 are accepted, default to 1. A different qml style file will be
        returned depending on the version
    :type qgis_version: int

    :param output_prefix: Base name for the shape file. Defaults to 'roads'
        which will result in an output file of 'roads.shp'.  Adding a
        prefix of e.g. 'test-' would result in a downloaded file name of
        'test-roads.shp'. Allowed characters are [a-zA-Z-_0-9].
    :type output_prefix: str

    :returns: Path to zipfile that was created.
    :rtype: str

    """
    work_dir = temp_dir(sub_dir=feature_type)
    directory_name = unique_filename(dir=work_dir)
    os.makedirs(directory_name)
    resource_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'resources', feature_type))
    style_file = os.path.join(resource_path, '%s.style' % feature_type)
    db_name = os.path.basename(directory_name)
    shape_path = os.path.join(directory_name, '%s.shp' % output_prefix)
    if qgis_version > 1:
        qml_source_path = os.path.join(
            resource_path, '%s.qml' % feature_type)
    else:
        qml_source_path = os.path.join(
            resource_path, '%s-qgis1.qml' % feature_type)
    qml_dest_path = os.path.join(
        directory_name, '%s.qml' % output_prefix)
    keywords_source_path = os.path.join(
        resource_path, '%s.keywords' % feature_type)
    keywords_dest_path = os.path.join(
        directory_name, '%s.keywords' % output_prefix)
    license_source_path = os.path.join(
        resource_path, '%s.license' % feature_type)
    license_dest_path = os.path.join(
        directory_name, '%s.license' % output_prefix)
    prj_source_path = os.path.join(
        resource_path, '%s.prj' % feature_type)
    prj_dest_path = os.path.join(
        directory_name, '%s.prj' % output_prefix)
    # Used to standarise types while data is in pg still
    transform_path = os.path.join(resource_path, 'transform.sql')
    createdb_executable = which('createdb')[0]
    createdb_command = '%s -T template_postgis %s' % (
        createdb_executable, db_name)
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
    add_keyword_timestamp(keywords_dest_path)
    # Now zip it up and return the path to the zip, removing the original shp
    zipfile = zip_shp(shape_path, extra_ext=[
        '.qml', '.keywords', '.license'], remove_file=True)
    print 'Shape written to %s' % shape_path
    return zipfile
