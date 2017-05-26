# coding=utf-8

"""
Views to handle url requests. Flask main entry point is also defined here.

:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""

import optparse
import xml
from flask import request, jsonify, render_template, Response, abort
# App declared directly in __init__ as per
# http://flask.pocoo.org/docs/patterns/packages/#larger-applications
from reporter import reporter
from reporter import config
from reporter.utilities import (
    split_bbox,
    osm_object_contributions,
    get_totals, osm_nodes_by_user)
from reporter.osm import (
    get_osm_file,
    import_and_extract_shapefile)
from reporter.exceptions import (
    OverpassTimeoutException,
    OverpassBadRequestException,
    OverpassConcurrentRequestException)
from reporter.queries import FEATURES, TAG_MAPPING
from reporter.static_files import static_file
from reporter import LOGGER
# noinspection PyPep8Naming
from urllib.error import URLError


@reporter.route('/')
def home():
    """Home page view.

    On this page a map and the report will be shown.
    """
    default_tag = 'highway'
    sorted_user_list = []
    bbox = request.args.get('bbox', config.BBOX)
    tag_name = request.args.get('obj', default_tag)
    date_from = request.args.get('date_from', None)
    date_to = request.args.get('date_to', None)
    error = None
    try:
        coordinates = split_bbox(bbox)
    except ValueError:
        error = "Invalid bbox"
        coordinates = split_bbox(config.BBOX)
    else:

        if tag_name not in list(TAG_MAPPING.keys()):
            error = "Unsupported object type"
            tag_name = default_tag
        try:
            feature_type = TAG_MAPPING[tag_name]
            file_handle = get_osm_file(
                coordinates,
                feature_type,
                'meta',
                date_from,
                date_to)
        except OverpassTimeoutException:
            error = 'Timeout, try a smaller area.'
        except OverpassBadRequestException:
            error = 'Bad request.'
        except OverpassConcurrentRequestException:
            error = 'Please try again later, another query is running.'
        except URLError:
            error = 'Bad request.'
        else:
            try:
                sorted_user_list = osm_object_contributions(
                    file_handle, tag_name)
            except xml.sax.SAXParseException:
                error = (
                    'Invalid OSM xml file retrieved. Please try again '
                    'later.')

    node_count, way_count = get_totals(sorted_user_list)

    # We need to manually cast float in string, otherwise floats are
    # truncated, and then rounds in Leaflet result in a wrong bbox
    # Note: slit_bbox should better keep returning real floats
    coordinates = dict((k, repr(v)) for k, v in coordinates.items())

    download_url = '%s-shp' % TAG_MAPPING[tag_name]
    context = dict(
        sorted_user_list=sorted_user_list,
        way_count=way_count,
        node_count=node_count,
        user_count=len(sorted_user_list),
        bbox=bbox,
        current_tag_name=tag_name,
        download_url=download_url,
        available_tag_names=list(TAG_MAPPING.keys()),
        error=error,
        coordinates=coordinates,
        display_update_control=int(config.DISPLAY_UPDATE_CONTROL),
    )
    # noinspection PyUnresolvedReferences
    return render_template('base.html', **context)


@reporter.route('/<feature_type>-shp')
def download_feature(feature_type):
    """Generic request to download OSM data.

    :param feature_type The feature to extract.
    :type feature_type str

    :return A zip file
    """
    if feature_type not in FEATURES:
        abort(404)

    bbox = request.args.get('bbox', config.BBOX)
    # Get the QGIS version
    # Currently 1, 2 are accepted, default to 2
    # A different qml style file will be returned depending on the version
    qgis_version = int(request.args.get('qgis_version', '2'))
    # Optional parameter that allows the user to specify the filename.
    output_prefix = request.args.get('output_prefix', feature_type)
    # A different keywords file will be returned depending on the version.
    inasafe_version = request.args.get('inasafe_version', None)
    # Optional parameter that allows the user to specify the language for
    # the legend in QGIS.
    lang = request.args.get('lang', 'en')

    # error = None
    try:
        coordinates = split_bbox(bbox)
    except ValueError:
        # error = "Invalid bbox"
        # coordinates = split_bbox(config.BBOX)
        abort(500)
    else:
        try:
            file_handle = get_osm_file(coordinates, feature_type, 'body')
        except OverpassTimeoutException:
            abort(408)
        except OverpassBadRequestException:
            abort(500)
        except OverpassConcurrentRequestException:
            abort(509)
        except URLError:
            abort(500)

    try:
        # noinspection PyUnboundLocalVariable
        zip_file = import_and_extract_shapefile(
            feature_type,
            file_handle.name,
            qgis_version,
            output_prefix,
            inasafe_version,
            lang)

        f = open(zip_file, 'rb')
    except IOError:
        abort(404)
        return
    return Response(f.read(), mimetype='application/zip')


@reporter.route('/user')
def user_status():
    """Get nodes for user as a json doc.

        .. note:: User from reporter.js

        To use e.g.:

        http://localhost:5000/user?bbox=20.431909561157227,
        -34.02849543118406,20.45207977294922,-34.02227106658948&
        obj=building&username=timlinux
    """
    username = request.args.get('username')
    bbox = request.args.get('bbox')

    try:
        coordinates = split_bbox(bbox)
    except ValueError:
        error = "Invalid bbox"
        coordinates = split_bbox(config.BBOX)
        LOGGER.exception(error + str(coordinates))
    else:
        try:
            file_handle = get_osm_file(coordinates)
        except OverpassTimeoutException:
            error = "Bad request. Maybe the bbox is too big!"
            LOGGER.exception(error + str(coordinates))
        except OverpassConcurrentRequestException:
            error = 'Please try again later, another query is running.'
            LOGGER.exception(error + str(coordinates))
        except OverpassBadRequestException:
            error = "Bad request."
            LOGGER.exception(error + str(coordinates))
        except URLError:
            error = "Bad request."
            LOGGER.exception(error + str(coordinates))
        else:
            node_data = osm_nodes_by_user(file_handle, username)
            return jsonify(d=node_data)
