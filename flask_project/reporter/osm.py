# coding=utf-8

"""
Module for low level OSM file retrieval.

:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""

import hashlib
import time
import os
import re
import sys
import datetime
from subprocess import call
from shutil import copyfile
from reporter.utilities import temp_dir, unique_filename, zip_shp, which
from reporter import config
from reporter import LOGGER
from reporter.queries import (
    SQL_QUERY_MAP,
    OVERPASS_QUERY_MAP,
    OVERPASS_QUERY_MAP_POLYGON
)
from reporter.utilities import (
    shapefile_resource_base_path,
    overpass_resource_base_path,
    generic_shapefile_base_path)
from reporter.exceptions import (
    OverpassTimeoutException,
    OverpassBadRequestException,
    OverpassConcurrentRequestException,
    OverpassDoesNotReturnData)
from reporter.metadata import metadata_files
from urllib.request import urlopen
# noinspection PyPep8Naming
from urllib.request import Request
from urllib.parse import quote, urlencode
import requests
# noinspection PyPep8Naming
from urllib.error import HTTPError

query_with_value = (
    '('
    'way["{key}"~"{value}"]'
    '(poly:"{polygon}");'
    'relation["{key}"~"{value}"]'
    '(poly:"{polygon}");'
    ');'
    '(._;>;);'
    'out {print_mode};'
)


def get_osm_file(
        coordinates,
        feature='all',
        overpass_verbosity='body',
        date_from=None,
        date_to=None,
        use_polygon=False):
    """Fetch an osm file given a bounding box using the overpass API.

    :param coordinates: Coordinates as a list in the form:
        [min lat, min lon, max lat, max lon]

    :param feature: The type of feature to extract:
        buildings, building-points, roads, potential-idp, boundary-[1,11]
    :type feature: str

    :param overpass_verbosity: Output verbosity in Overpass.
        It can be body, skeleton, ids_only or meta.
    :type overpass_verbosity: str

    :param date_from: First date for date range.
    :type date_from: str

    :param date_to: Second date for date range.
    :type date_to: str

    :param use_polygon: Flag if coordinates is polygon or bbox
    :type use_polygon: bool

    :returns: A file which has been opened on the retrieved OSM dataset.
    :rtype: file

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
    server_url = 'http://overpass-api.de/api/interpreter?data='
    parameters = dict()
    parameters['print_mode'] = overpass_verbosity

    if use_polygon:
        parameters['polygon'] = coordinates
    else:
        parameters.update(coordinates)

    if '=' in feature:
        feature_keys = feature.split('=')
        parameters['key'] = feature_keys[0]
        parameters['value'] = feature_keys[1].replace(',', '|')
        query = query_with_value.format(**parameters)
    else:
        if use_polygon:
            query = OVERPASS_QUERY_MAP_POLYGON[feature].format(**parameters)
        else:
            query = OVERPASS_QUERY_MAP[feature].format(**parameters)

    if date_from and date_to:
        try:
            datetime_from = datetime.datetime.utcfromtimestamp(
                float(date_from) / 1000.)
            datetime_to = datetime.datetime.utcfromtimestamp(
                float(date_to) / 1000.)
            date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
            diff_query = '[diff:"{date_from}", "{date_to}"];'.format(
                date_from=datetime_from.strftime(date_format),
                date_to=datetime_to.strftime(date_format)
            )
            query = diff_query + query
        except ValueError as e:
            LOGGER.debug(e)

    encoded_query = quote(query)
    url_path = '%s%s' % (server_url, encoded_query)
    safe_name = hashlib.md5(query.encode('utf-8')).hexdigest() + '.osm'
    file_path = os.path.join(config.CACHE_DIR, safe_name)
    return load_osm_document(file_path, url_path)


def load_osm_document(file_path, url_path):
    """Load an osm document, refreshing it if the cached copy is stale.

    To save bandwidth the file is not downloaded if it is less than 1 hour old.

    :type file_path: basestring
    :param file_path: The path on the filesystem to which the file should
        be saved.

    :param url_path: Path (relative to the ftp root) from which the file
        should be retrieved.
    :type url_path: str

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


def fetch_osm_with_post(file_path, url_path, post_data, returns_format='json'):
    """Fetch an osm map and store locally.

    :param url_path: The path (relative to the ftp root) from which the
        file should be retrieved.
    :type url_path: str

    :param file_path: The path on the filesystem to which the file should
        be saved.
    :type file_path: str

    :param post_data: Overpass data
    :type post_data: str

    :param returns_format: Format of the response, could be json or xml
    :type returns_format: str

    :returns: The path to the downloaded file.

    """
    headers = {'User-Agent': 'HotOSM'}
    try:
        data = requests.post(
                url=url_path,
                data={'data': post_data},
                headers=headers)

        if returns_format != 'xml':
            regex = '<remark> runtime error:'
            if re.search(regex, data.text):
                raise OverpassTimeoutException

            regex = '(elements|meta)'
            if not re.search(regex, data.text):
                raise OverpassDoesNotReturnData

        if os.path.exists(file_path):
            os.remove(file_path)

        file_handle = open(file_path, 'wb')
        file_handle.write(data.text.encode('utf-8'))
        file_handle.close()
    except HTTPError as e:
        if e.code == 400:
            LOGGER.exception('Bad request to Overpass')
            raise OverpassBadRequestException
        elif e.code == 419:
            raise OverpassConcurrentRequestException

        LOGGER.exception('Error with Overpass')
        raise e


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
    headers = {'User-Agent': 'InaSAFE'}
    web_request = Request(url_path, None, headers)
    try:
        url_handle = urlopen(web_request, timeout=60)
        data = url_handle.read().decode('utf-8')
        regex = '<remark> runtime error:'
        if re.search(regex, data):
            raise OverpassTimeoutException

        regex = '(elements|meta)'
        if not re.search(regex, data):
            raise OverpassDoesNotReturnData

        if os.path.exists(file_path):
            os.remove(file_path)

        file_handle = open(file_path, 'wb')
        file_handle.write(data.encode('utf-8'))
        file_handle.close()
    except HTTPError as e:
        if e.code == 400:
            LOGGER.exception('Bad request to Overpass')
            raise OverpassBadRequestException
        elif e.code == 419:
            raise OverpassConcurrentRequestException

        LOGGER.exception('Error with Overpass')
        raise e


def add_metadata_timestamp(metadata_file_path):
    """Add the current date / time to the metadata file.

    :param metadata_file_path: Metadata file path that the timestamp should be
        written to.
    :type metadata_file_path: str
    """
    time_stamp = time.strftime('%d-%m-%Y %H:%M')

    extension = os.path.splitext(metadata_file_path)[1]

    if extension == 'keywords':
        keyword_file = open(metadata_file_path, 'ab')
        content = 'date: %s' % time_stamp
        keyword_file.write(content.encode('utf-8'))
        keyword_file.close()
    else:
        # Need to write this section : write date/time in XML file
        # {{ datetime }} -> 18-06-2018 03:23
        f = open(metadata_file_path, 'r')
        file_data = f.read()
        f.close()

        new_data = file_data.replace('{{ datetime }}', time_stamp)

        f = open(metadata_file_path, 'w')
        f.write(new_data)
        f.close()


def import_and_extract_shapefile(
        feature_type,
        file_path,
        qgis_version=2,
        output_prefix='',
        inasafe_version=None,
        lang='en'):
    """Convert the OSM xml file to a shapefile.

    This is a multi-step process:
        * Create a temporary postgis database
        * Load the osm dataset into POSTGIS with osm2pgsql and our custom
             style file.
        * Save the data out again to a shapefile
        * Zip the shapefile ready for user to download

    :param feature_type: The feature to extract.
    :type feature_type: str

    :param file_path: Path to the OSM file name.
    :type file_path: str

    :param qgis_version: Get the QGIS version. Currently 1,
        2 are accepted, default to 2. A different qml style file will be
        returned depending on the version
    :type qgis_version: int

    :param output_prefix: Base name for the shape file. Defaults to ''
        which will result in an output file of feature_type + '.shp'. Adding a
        prefix of e.g. 'test-' would result in a downloaded file name of
        'test-buildings.shp'. Allowed characters are [a-zA-Z-_0-9].
    :type output_prefix: str

    :param inasafe_version: The InaSAFE version, to get correct metadata.
    :type inasafe_version: str

    :param lang: The language desired for the labels in the legend.
        Example : 'en', 'fr', etc. Default is 'en'.
    :type lang: str

    :returns: Path to zipfile that was created.
    :rtype: str

    """
    if not check_string(output_prefix):
        error = 'Invalid output prefix: %s' % output_prefix
        LOGGER.exception(error)
        raise Exception(error)

    output_prefix += feature_type

    work_dir = temp_dir(sub_dir=feature_type)
    directory_name = unique_filename(dir=work_dir)
    db_name = os.path.basename(directory_name)

    import_osm_file(db_name, feature_type, file_path)
    zip_file = extract_shapefile(
        feature_type,
        db_name,
        directory_name,
        qgis_version,
        output_prefix,
        inasafe_version,
        lang)
    drop_database(db_name)
    return zip_file


def import_osm_file(db_name, feature_type, file_path):
    """Import the OSM xml file into a postgis database.

    :param db_name: The database to use.
    :type db_name: str

    :param feature_type: The feature to import.
    :type feature_type: str

    :param file_path: Path to the OSM file.
    :type file_path: str
    """
    overpass_resource_path = overpass_resource_base_path(feature_type)
    style_file = '%s.style' % overpass_resource_path

    # Used to standarise types while data is in pg still
    transform_path = '%s.sql' % overpass_resource_path
    createdb_executable = which('createdb')[0]
    createdb_command = '%s -T template_postgis %s' % (
        createdb_executable, db_name)
    osm2pgsql_executable = which('osm2pgsql')[0]
    osm2pgsql_options = config.OSM2PGSQL_OPTIONS
    osm2pgsql_command = '%s -S %s -d %s %s %s' % (
        osm2pgsql_executable,
        style_file,
        db_name,
        osm2pgsql_options,
        file_path)
    psql_executable = which('psql')[0]
    transform_command = '%s %s -f %s' % (
        psql_executable, db_name, transform_path)

    LOGGER.info(createdb_command)
    call(createdb_command, shell=True)
    LOGGER.info(osm2pgsql_command)
    call(osm2pgsql_command, shell=True)
    LOGGER.info(transform_command)
    call(transform_command, shell=True)


def drop_database(db_name):
    """Remove a database.

    :param db_name: The database
    :type db_name: str
    """
    dropdb_executable = which('dropdb')[0]
    dropdb_command = '%s %s' % (dropdb_executable, db_name)
    LOGGER.info(dropdb_command)
    call(dropdb_command, shell=True)


def extract_shapefile(
        feature_type,
        db_name,
        directory_name,
        qgis_version=2,
        output_prefix='',
        inasafe_version=None,
        lang='en'):
    """Extract a database to a shapefile.

    This is a multi-step process:
        * Create a temporary postgis database
        * Load the osm dataset into POSTGIS with osm2pgsql and our custom
             style file.
        * Save the data out again to a shapefile
        * Zip the shapefile ready for user to download

    :param feature_type: The feature to extract.
    :type feature_type: str

    :param db_name: The database to extract.
    :type db_name: str

    :param directory_name: The directory to use for the extract.
    :type directory_name: str

    :param qgis_version: Get the QGIS version. Currently 1,
        2 are accepted, default to 2. A different qml style file will be
        returned depending on the version
    :type qgis_version: int

    :param output_prefix: Base name for the shape file. Defaults to ''
        which will result in an output file of feature_type + '.shp'. Adding a
        prefix of e.g. 'test-' would result in a downloaded file name of
        'test-buildings.shp'. Allowed characters are [a-zA-Z-_0-9].
    :type output_prefix: str

    :param inasafe_version: The InaSAFE version, to get correct metadata.
    :type inasafe_version: str

    :param lang: The language desired for the labels in the legend.
        Example : 'en', 'fr', etc. Default is 'en'.
    :type lang: str

    :returns: Path to zipfile that was created.
    :rtype: str
    """
    # Extract
    os.makedirs(directory_name)
    shapefile_resource_path = shapefile_resource_base_path(feature_type)

    shape_path = os.path.join(directory_name, '%s.shp' % output_prefix)

    if qgis_version > 1:
        qml_source_path = '%s-%s.qml' % (shapefile_resource_path, lang)
        if not os.path.isfile(qml_source_path):
            qml_source_path = '%s-en.qml' % shapefile_resource_path
    else:
        qml_source_path = '%s-qgis1.qml' % shapefile_resource_path

    qml_dest_path = os.path.join(directory_name, '%s.qml' % output_prefix)

    license_source_path = '%s.license' % generic_shapefile_base_path()
    license_dest_path = os.path.join(
        directory_name, '%s.license' % output_prefix)
    prj_source_path = '%s.prj' % generic_shapefile_base_path()
    prj_dest_path = os.path.join(
        directory_name, '%s.prj' % output_prefix)

    pgsql2shp_executable = which('pgsql2shp')[0]
    pgsql2shp_command = '%s -f %s %s %s' % (
        pgsql2shp_executable, shape_path, db_name, SQL_QUERY_MAP[feature_type])

    # Now run the commands in sequence:
    LOGGER.info(pgsql2shp_command)
    call(pgsql2shp_command, shell=True)
    copyfile(qml_source_path, qml_dest_path)

    metadata = metadata_files(
        inasafe_version, lang, feature_type, output_prefix)

    for destination, source in metadata.items():
        source_path = '%s%s' % (shapefile_resource_path, source)
        destination_path = os.path.join(directory_name, destination)
        copyfile(source_path, destination_path)
        add_metadata_timestamp(destination_path)

    # Generic files
    copyfile(prj_source_path, prj_dest_path)
    copyfile(license_source_path, license_dest_path)

    # Now zip it up and return the path to the zip, removing the original shp
    zipfile = zip_shp(
        shape_path,
        extra_ext=['.qml', '.keywords', '.license', '.xml'],
        remove_file=True)
    LOGGER.info('Shape written to {path}'.format(path=shape_path))

    return zipfile


def check_string(text, search=re.compile(r'[^A-Za-z0-9-_]').search):
    """Test that a string doesnt contain unwanted characters.

    :param text: Text that you want to verify is compliant.
    :type text: str

    :param search: Regex to use to check the string. Defaults to allowing
        [^a-z0-9-_].

    :return: bool
    """
    return not bool(search(text))
