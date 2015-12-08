# coding=utf-8
"""Views to handle url requests. Flask main entry point is also defined here.
:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""

import urllib2
import optparse
import xml

from flask import request, jsonify, render_template, Response, abort
# App declared directly in __init__ as per
# http://flask.pocoo.org/docs/patterns/packages/#larger-applications
from . import app
from . import config
from .utilities import (
    split_bbox,
    osm_object_contributions,
    get_totals, osm_nodes_by_user)
from .osm import (
    get_osm_file,
    extract_shapefile)
from .static import static_file
from . import LOGGER


@app.route('/')
def home():
    """Home page view.

    On this page a map and the report will be shown.
    """
    sorted_user_list = []
    bbox = request.args.get('bbox', config.BBOX)
    tag_name = request.args.get('obj', config.TAG_NAMES[0])
    error = None
    try:
        coordinates = split_bbox(bbox)
    except ValueError:
        error = "Invalid bbox"
        coordinates = split_bbox(config.BBOX)
    else:
        try:
            feature_type = 'all'
            file_handle = get_osm_file(coordinates, feature_type)
        except urllib2.URLError:
            error = "Bad request. Maybe the bbox is too big!"
        else:
            if tag_name not in config.TAG_NAMES:
                error = "Unsupported object type"
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
    coordinates = dict((k, repr(v)) for k, v in coordinates.iteritems())

    context = dict(
        sorted_user_list=sorted_user_list,
        way_count=way_count,
        node_count=node_count,
        user_count=len(sorted_user_list),
        bbox=bbox,
        current_tag_name=tag_name,
        available_tag_names=config.TAG_NAMES,
        error=error,
        coordinates=coordinates,
        display_update_control=int(config.DISPLAY_UPDATE_CONTROL),
    )
    # noinspection PyUnresolvedReferences
    return render_template('base.html', **context)


def osm_download_request(url_request, feature_type):
    """Generic request to download OSM data.

    :param url_request The request.
    :type url_request RequestContext

    :param feature_type The feature to extract.
    :type feature_type str

    :return A zip file
    """
    bbox = url_request.args.get('bbox', config.BBOX)
    # Get the QGIS version
    # Currently 1, 2 are accepted, default to 2
    # A different qml style file will be returned depending on the version
    qgis_version = int(url_request.args.get('qgis_version', '2'))
    # Optional parameter that allows the user to specify the filename.
    output_prefix = url_request.args.get('output_prefix', feature_type)
    # A different keywords file will be returned depending on the version.
    inasafe_version = url_request.args.get('inasafe_version', None)
    # Optional parameter that allows the user to specify the language for
    # the legend in QGIS.
    lang = url_request.args.get('lang', 'en')

    # error = None
    try:
        coordinates = split_bbox(bbox)
    except ValueError:
        # error = "Invalid bbox"
        # coordinates = split_bbox(config.BBOX)
        abort(500)
    else:
        try:
            file_handle = get_osm_file(coordinates, feature_type)
        except urllib2.URLError:
            # error = "Bad request. Maybe the bbox is too big!"
            abort(500)

    try:
        # noinspection PyUnboundLocalVariable
        zip_file = extract_shapefile(
            feature_type,
            file_handle.name,
            qgis_version,
            output_prefix,
            inasafe_version,
            lang)

        f = open(zip_file)
    except IOError:
        abort(404)
        return
    return Response(f.read(), mimetype='application/zip')


@app.route('/roads-shp')
def roads():
    """View to download roads as a shp."""
    feature_type = 'roads'
    return osm_download_request(request, feature_type)


@app.route('/potential-idp-shp')
def potential_idp():
    """View to download potential idp as a shp.

    ..deprecated:: Use :func:`evacuation_center` instead.
    """
    feature_type = 'potential-idp'
    return osm_download_request(request, feature_type)


@app.route('/evacuation-centers-shp')
def evacuation_center():
    """View to download evacuation center as a shp."""
    feature_type = 'evacuation-center'
    return osm_download_request(request, feature_type)


@app.route('/buildings-shp')
def buildings():
    """View to download buildings as a shp."""
    feature_type = 'buildings'
    return osm_download_request(request, feature_type)


@app.route('/building-points-shp')
def building_points():
    """View to download building points as a shp."""
    feature_type = 'building-points'
    return osm_download_request(request, feature_type)


@app.route('/flood-prone-shp')
def flood_prone():
    """View to download flood prone as a shp."""
    feature_type = 'flood-prone'
    return osm_download_request(request, feature_type)


@app.route('/boundary-1-shp')
def boundary_1():
    """View to download admin_level 1 boundaries as a shp."""
    feature_type = 'boundary-1'
    return osm_download_request(request, feature_type)


@app.route('/boundary-2-shp')
def boundary_2():
    """View to download admin_level 2 boundaries as a shp."""
    feature_type = 'boundary-2'
    return osm_download_request(request, feature_type)


@app.route('/boundary-3-shp')
def boundary_3():
    """View to download admin_level 3 boundaries as a shp."""
    feature_type = 'boundary-3'
    return osm_download_request(request, feature_type)


@app.route('/boundary-4-shp')
def boundary_4():
    """View to download admin_level 4 boundaries as a shp."""
    feature_type = 'boundary-4'
    return osm_download_request(request, feature_type)


@app.route('/boundary-5-shp')
def boundary_5():
    """View to download admin_level 5 boundaries as a shp."""
    feature_type = 'boundary-5'
    return osm_download_request(request, feature_type)


@app.route('/boundary-6-shp')
def boundary_6():
    """View to download admin_level 6 boundaries as a shp."""
    feature_type = 'boundary-6'
    return osm_download_request(request, feature_type)


@app.route('/boundary-7-shp')
def boundary_7():
    """View to download admin_level 7 boundaries as a shp."""
    feature_type = 'boundary-7'
    return osm_download_request(request, feature_type)


@app.route('/boundary-8-shp')
def boundary_8():
    """View to download admin_level 8 boundaries as a shp."""
    feature_type = 'boundary-8'
    return osm_download_request(request, feature_type)

@app.route('/boundary-9-shp')
def boundary_9():
    """View to download admin_level 9 boundaries as a shp."""
    feature_type = 'boundary-9'
    return osm_download_request(request, feature_type)


@app.route('/boundary-10-shp')
def boundary_10():
    """View to download admin_level 10 boundaries as a shp."""
    feature_type = 'boundary-10'
    return osm_download_request(request, feature_type)


@app.route('/boundary-11-shp')
def boundary_11():
    """View to download admin_level 11 boundaries as a shp."""
    feature_type = 'boundary-11'
    return osm_download_request(request, feature_type)


@app.route('/user')
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
        except urllib2.URLError:
            error = "Bad request. Maybe the bbox is too big!"
            LOGGER.exception(error + str(coordinates))
        else:
            node_data = osm_nodes_by_user(file_handle, username)
            return jsonify(d=node_data)


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
