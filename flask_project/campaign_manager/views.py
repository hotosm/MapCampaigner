import base64
import csv
import inspect
import json
import os
import hashlib
import requests
import shutil
from simplekml import Kml, ExtendedData
from datetime import datetime
from flask import jsonify
from shapely import geometry as shapely_geometry

from urllib import request as urllibrequest
from urllib.error import HTTPError, URLError

from bs4 import BeautifulSoup
from flask import (
    request,
    render_template,
    Response,
    abort,
    send_file,
    send_from_directory
)

from app_config import Config
from campaign_manager import campaign_manager
from campaign_manager.utilities import (
    get_types,
    map_provider,
    get_allowed_managers,
    parse_json_string
)
import campaign_manager.insights_functions as insights_functions
from campaign_manager.insights_functions._abstract_insights_function import (
    AbstractInsightsFunction
)
from campaign_manager.utilities import temporary_folder
from campaign_manager.data_providers.tasking_manager import \
    TaskingManagerProvider
from campaign_manager.api import CampaignNearestList, CampaignList
from campaign_manager.models.campaign import Campaign, Permission
from campaign_manager.models.survey import Survey
from campaign_manager.insights_functions.osmcha_changesets import \
    OsmchaChangesets

from campaign_manager.data_providers.overpass_provider import OverpassProvider
from reporter import config
from campaign_manager.utilities import (
    load_osm_document_cached, get_contribs, geojson_to_gpx
)
from reporter import LOGGER
from reporter.static_files import static_file
from campaign_manager.aws import S3Data

from xml.sax.saxutils import escape


try:
    from secret import OAUTH_CONSUMER_KEY, OAUTH_SECRET
except ImportError:
    try:
        OAUTH_CONSUMER_KEY = os.environ['OAUTH_CONSUMER_KEY']
        OAUTH_SECRET = os.environ['OAUTH_SECRET']
    except KeyError:
        OAUTH_CONSUMER_KEY = ''
        OAUTH_SECRET = ''

MAX_AREA_SIZE = 320000000


@campaign_manager.route('/')
def home():
    """Landing page

    The first page users land on when they use the app.
    """

    context = dict(
        oauth_consumer_key=OAUTH_CONSUMER_KEY,
        oauth_secret=OAUTH_SECRET,
        map_provider=map_provider()
    )

    return render_template('home.html', **context)


@campaign_manager.route('/learn')
def learn():
    """MapCampaigner Docs

    Information about to use MapCampaigner.
    """

    context = dict(
        oauth_consumer_key=OAUTH_CONSUMER_KEY,
        oauth_secret=OAUTH_SECRET,
        map_provider=map_provider()
    )

    return render_template('learn.html', **context)


@campaign_manager.route('/styleguide')
def styleguide():
    """Styleguide

    This page shows a library of UI components.
    """

    context = dict(
        oauth_consumer_key=OAUTH_CONSUMER_KEY,
        oauth_secret=OAUTH_SECRET,
        map_provider=map_provider()
    )

    return render_template('styleguide.html', **context)


@campaign_manager.route('/user/<osm_id>')
def campaigns_list(osm_id):
    """List the user's campaigns

    A summary campaign manager view with all the users campaigns
    """

    context = dict(
        oauth_consumer_key=OAUTH_CONSUMER_KEY,
        oauth_secret=OAUTH_SECRET,
        all=True,
        map_provider=map_provider(),
        bucket_url=S3Data().bucket_url(),
        osm_id=osm_id
    )

    return render_template('campaign_index.html', **context)


def clean_argument(args):
    """Clean argument that is ImmutableMultiDict to dict
    and clean it's value
    :param args: Argument from request
    :type args: ImmutableMultiDict

    :type: clean argument
    :rtype: dict
    """

    arguments = dict(args)
    clean_arguments = {}
    for key, value in arguments.items():
        if len(value) == 1:
            value = value[0]
        clean_arguments[key] = value
    return clean_arguments


@campaign_manager.route('/campaign/<uuid>/<insight_function_id>')
def get_campaign_insight_function_data(uuid, insight_function_id):
    """Get campaign insight function data.
    """
    return Response("", 200)


@campaign_manager.route('/campaign/osmcha_errors/<uuid>')
def get_osmcha_errors_function(uuid):
    try:
        campaign = Campaign.get(uuid)
        rendered_html = campaign.render_insights_function(
            insight_function_id='total-osmcha-errors',
            insight_function_name='OsmchaChangesets',
            additional_data=clean_argument(request.args)
        )
        return Response(rendered_html)
    except Campaign.DoesNotExist:
        abort(404)


@campaign_manager.route('/campaign/osmcha_errors_data/<uuid>')
def get_osmcha_errors_data(uuid):
    try:
        campaign = Campaign.get(uuid)
        page_size = request.args.get('page_size', None)
        page = request.args.get('page', None)
        osmcha_changeset = OsmchaChangesets(campaign=campaign)

        if page_size:
            osmcha_changeset.max_page = int(page_size)
        if page:
            osmcha_changeset.current_page = int(page)

        osmcha_changeset.run()
        data = osmcha_changeset.get_function_data()
        return jsonify(data)
    except Campaign.DoesNotExist:
        abort(404)


def check_geojson_is_polygon(geojson):
    """Checking geojson is polygon"""
    types = ["Polygon", "MultiPolygon"]
    for feature in geojson['features']:
        if feature['geometry'] and feature['geometry']['type'] not in types:
            return False
    return True


@campaign_manager.route('/campaign/<uuid>/boundary-upload-success')
def campaign_boundary_upload_chunk_success(uuid):
    """Upload chunk handle success.
    """
    from campaign_manager.models.campaign import Campaign
    from campaign_manager.data_providers.shapefile_provider import \
        ShapefileProvider
    # validate boundary
    try:
        # folder for this campaign
        folder = os.path.join(
            temporary_folder(),
            uuid
        )
        shapefile_file = "%s/%s.shp" % (
            folder, uuid
        )
        geojson = ShapefileProvider().get_data(shapefile_file)

        if len(geojson['features']) > 1:
            # TODO : Check if polygons unionable
            pass

        if geojson['features'][0]['geometry']['type'] != 'Polygon':
            raise ShapefileProvider.MultiPolygonFound

        if not geojson:
            if os.path.exists(folder):
                shutil.rmtree(folder)
            return Response(json.dumps({
                'success': False,
                'reason': 'Shapefile is not valid.'
            }))
        if not check_geojson_is_polygon(geojson):
            if os.path.exists(folder):
                shutil.rmtree(folder)
            return Response(json.dumps({
                'success': False,
                'reason': 'It is not in polygon/multipolygon type.'
            }))

        if os.path.exists(folder):
            shutil.rmtree(folder)
        return Response(json.dumps({
            'success': True,
            'data': geojson,
        }))
    except Campaign.DoesNotExist:
        abort(404)
    except ShapefileProvider.MultiPolygonFound as e:
        return Response(json.dumps({
            'success': False,
            'reason': e.message
        }))


def upload_chunk(_file, filename):
    """Upload chunk file for specific folder.
    :param _file: file to be saved

    :param filename:filename path to be saved
    :type filename: src
    """

    # save uploaded file
    if 'Content-Range' in request.headers:
        range_str = request.headers['Content-Range']
        start_bytes = int(range_str.split(' ')[1].split('-')[0])
        # remove old file if upload new file
        if start_bytes == 0:
            if os.path.exists(filename):
                os.remove(filename)

        # append chunk to the file on disk, or create new
        with open(filename, 'ab') as f:
            f.seek(start_bytes)
            f.write(_file.read())

    else:
        # this is not a chunked request, so just save the whole file
        _file.save(filename)

    # send response with appropriate mime type header
    return Response(json.dumps({
        "name": _file.filename,
        "size": os.path.getsize(filename),
        "url": 'uploads/' + _file.filename,
        "thumbnail_url": None,
        "delete_url": None,
        "delete_type": None
    }))


@campaign_manager.route(
    '/campaign/<uuid>/coverage-upload-chunk',
    methods=['POST'])
def campaign_coverage_upload_chunk(uuid):
    from campaign_manager.models.campaign import Campaign
    """Upload chunk handle.
    """
    try:
        _file = request.files['file']
        filename = _file.filename
        filenames = os.path.splitext(filename)
        # folder for this campaign
        filename = os.path.join(
            Config.campaigner_data_folder,
            'coverage',
            uuid
        )
        if not os.path.exists(filename):
            os.mkdir(filename)

        # filename of coverage
        filename = os.path.join(
            filename,
            '%s%s' % (
                uuid,
                filenames[1] if len(filenames) > 1 else ''
            )
        )
        return upload_chunk(_file, filename)
    except Campaign.DoesNotExist:
        abort(404)


@campaign_manager.route(
    '/campaign/<uuid>/boundary-upload-chunk',
    methods=['POST'])
def campaign_boundary_upload_chunk(uuid):
    from campaign_manager.models.campaign import Campaign
    """Upload chunk handle.
    """
    try:
        _file = request.files['file']
        filename = _file.filename
        filenames = os.path.splitext(filename)
        # folder for this campaign
        filename = os.path.join(
            temporary_folder(),
            uuid
        )
        if not os.path.exists(filename):
            os.mkdir(filename)

        # filename of coverage
        filename = os.path.join(
            filename,
            '%s%s' % (
                uuid,
                filenames[1] if len(filenames) > 1 else ''
            )
        )
        return upload_chunk(_file, filename)
    except Campaign.DoesNotExist:
        abort(404)


def get_campaign_data(uuid):
    from campaign_manager.models.campaign import Campaign
    from campaign_manager.aws import S3Data
    """Get campaign details.
    """
    try:
        campaign = Campaign.get(uuid)
    except:
        abort(404)

    context = campaign.to_dict()
    context['s3_campaign_url'] = S3Data().url(uuid)

    campaign_manager_names = []
    for manager in parse_json_string(campaign.campaign_managers):
        campaign_manager_names.append(manager['name'])

    campaign_viewer_names = []
    for viewer in parse_json_string(campaign.campaign_viewers):
        campaign_viewer_names.append(viewer['name'])

    campaign_contributor_names = []
    for contributor in parse_json_string(campaign.campaign_contributors):
        campaign_contributor_names.append(contributor['name'])

    context['oauth_consumer_key'] = OAUTH_CONSUMER_KEY
    context['oauth_secret'] = OAUTH_SECRET
    context['map_provider'] = map_provider()
    context['campaign_manager_names'] = campaign_manager_names
    context['campaign_viewer_names'] = campaign_viewer_names
    context['campaign_contributor_names'] = campaign_contributor_names
    context['participants'] = len(campaign.campaign_managers)

    context['pct_covered_areas'] = campaign.calculate_areas_covered()

    if campaign.map_type != '':
        context['attribution'] = find_attribution(campaign.map_type)

    # Start date
    try:
        start_date = datetime.strptime(campaign.start_date, '%Y-%m-%d')
        context['start_date_date'] = start_date.strftime('%d %b')
        context['start_date_year'] = start_date.strftime('%Y')
    except TypeError:
        context['start_date_date'] = '-'
        context['start_date_year'] = '-'
    context['current_status'] = campaign.get_current_status()
    if context['current_status'] == 'active':
        context['current_status'] = 'running'

    # End date
    try:
        end_date = datetime.strptime(campaign.end_date, '%Y-%m-%d')
        context['end_date_date'] = end_date.strftime('%d %b')
        context['end_date_year'] = end_date.strftime('%Y')
    except TypeError:
        context['end_date_date'] = '-'
        context['end_date_year'] = '-'
    return context


@campaign_manager.route('/campaign/<uuid>')
def get_campaign(uuid):
    context = get_campaign_data(uuid)
    context['types'] = list(map(lambda type:
      type[1]['type'],
      context['types'].items()))
    return render_template('campaign_detail.html', **context)


@campaign_manager.route('/campaign/<uuid>/features')
def get_campaign_features(uuid):
    context = get_campaign_data(uuid)
    return render_template('campaign_features.html', **context)


def get_type_details(types, feature_name):
    for key, value in types.items():
        if value['type'].replace(" ", "_") == feature_name:
            return value


@campaign_manager.route('/campaign/<uuid>/features/<feature_name>')
def get_feature_details(uuid, feature_name):
    context = get_campaign_data(uuid)
    context['feature_name'] = feature_name
    context['feature_details'] = get_type_details(
        context['types'],
        feature_name)
    return render_template('feature_details.html', **context)


@campaign_manager.route('/campaign/<uuid>/contributors')
def get_campaign_contributors(uuid):
    context = get_campaign_data(uuid)
    return render_template('campaign_contributors.html', **context)


@campaign_manager.route('/campaign/<uuid>/area')
def get_campaign_area(uuid):
    context = get_campaign_data(uuid)
    return render_template('campaign_area.html', **context)


@campaign_manager.route('/participate')
def participate():
    from flask import url_for, redirect
    """Action from participate button, return nearest/recent/active campaign.
    """
    campaign_to_participate = None
    campaigns = []
    user_coordinate = request.args.get('coordinate', None)
    campaign_status = 'active'

    if user_coordinate:
        # Get nearest campaign
        campaigns = CampaignNearestList(). \
            get_nearest_campaigns(user_coordinate, campaign_status)
    if not user_coordinate or len(campaigns) < 1:
        campaigns = CampaignList().get_all_campaign(campaign_status)

    # Get most recent
    for campaign in campaigns:
        if not campaign_to_participate:
            campaign_to_participate = campaign
            continue

        campaign_edited_date = datetime.strptime(
            campaign_to_participate.edited_at,
            '%a %b %d %H:%M:%S %Y'
        )

        campaign_to_compare = datetime.strptime(
            campaign.edited_at,
            '%a %b %d %H:%M:%S %Y'
        )

        if campaign_to_compare > campaign_edited_date:
            campaign_to_participate = campaign

    if campaign_to_participate:
        return redirect(
                url_for('campaign_manager.get_campaign',
                        uuid=campaign_to_participate.uuid)
        )
    else:
        abort(404)


@campaign_manager.route('/gpx/<json_data>', methods=['GET'])
def generate_gpx(json_data):
    # decoding to geojson
    try:
        decoded_json = base64.b64decode(json_data).decode('utf-8')
    except UnicodeDecodeError:
        abort(400)

    geojson = json.loads(decoded_json)
    xml_gpx = geojson_to_gpx(geojson)

    resp = Response(xml_gpx, mimetype='text/xml', status=200)
    cors_host = 'https://www.openstreetmap.org'
    # Disable CORS.
    resp.headers['Access-Control-Allow-Origin'] = cors_host

    return r


@campaign_manager.route('/mbtiles', methods=['POST'])
def get_mbtile():
    # decoding to geojson
    client = S3Data()

    coords = json.loads(request.values.get('coordinates'))
    polygon = shapely_geometry.Polygon(coords)

    url = 'campaigns/{0}/mbtiles/'.format(request.values.get('uuid'))

    mbtiles = client.fetch('{0}tiles.geojson'.format(url))

    # Get all campaign polygons.
    features = [f for f in mbtiles['features']
        if f['properties']['parent'] is None]
    polygons = [shapely_geometry.Polygon(f['geometry']['coordinates'][0])
        for f in features]
    polygons = [shapely_geometry.polygon.orient(p) for p in polygons]
    centroids = [p.centroid for p in polygons]

    distances = [polygon.centroid.distance(c) for c in centroids]
    min_distance = distances.index(min(distances))

    tiles_id = features[min_distance]['properties']['id']
    tiles_file = '{0}.mbtiles'.format(tiles_id)

    # Get file from s3
    file_path = '{0}{1}'.format(url, tiles_file)
    aws_url = 'https://s3-us-west-2.amazonaws.com'
    file_url = '{0}/{1}/{2}'.format(aws_url, client.bucket, file_path)

    return Response(json.dumps({'file_url': file_url}))


@campaign_manager.route('/generate_josm', methods=['POST'])
def generate_josm():
    """Get overpass xml data from ids store it to temporary folder."""
    error_features = request.values.get('error_features', None)
    if not error_features:
        abort(404)

    server_url = 'http://overpass.hotosm.org/api/' \
                 'interpreter'
    error_features = json.loads(error_features)
    element_query = OverpassProvider().parse_url_parameters(
        element_ids=error_features
    )
    safe_name = hashlib.md5(
            element_query.encode('utf-8')).hexdigest() + '_josm.osm'
    file_path = os.path.join(config.CACHE_DIR, safe_name)
    osm_data, osm_doc_time, updating = load_osm_document_cached(
            file_path, server_url, element_query, False)
    if osm_data:
        return Response(json.dumps({'file_name': safe_name}))


@campaign_manager.route('/download_josm/<uuid>/<file_name>')
def download_josm(uuid, file_name):
    """Download josm file."""
    campaign = Campaign.get(uuid)
    campaign_name = campaign.name + '.osm'
    file_path = os.path.join(config.CACHE_DIR, file_name)
    if not os.path.exists(file_path):
        abort(404)
    return send_file(
            file_path,
            as_attachment=True,
            attachment_filename=campaign_name)


@campaign_manager.route('/generate_csv', methods=['GET'])
def generate_csv():
    types = request.values.get('types').split(',')
    url = request.values.get('campaign_url')
    uuid = request.values.get('uuid')

    csv_data = [get_contribs(url, t) for t in types]

    # Remove None values.
    csv_data = [t for t in csv_data if t is not None]

    # Flatten again to create only a single list.
    csv_data = [item for sublist in csv_data for item in sublist]

    file_name = '{0}.csv'.format(uuid)
    file_path = os.path.join(config.CACHE_DIR, file_name)

    # Remove repeated rows.
    csv_data = list(set([tuple(d) for d in csv_data]))
    csv_data.sort()

    # Append headers.
    headers = ('user', 'type', 'date', 'no_contribs')
    csv_data = [headers] + csv_data

    with open(file_path, 'w', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)

    resp_dict = {'file_name': file_name, 'uuid': uuid}

    return Response(json.dumps(resp_dict))


@campaign_manager.route('/download_csv/<uuid>/<file_name>')
def download_csv(uuid, file_name):
    file_path = os.path.join(config.CACHE_DIR, file_name)
    if not os.path.exists(file_path):
        abort(404)

    return send_file(
        file_path,
        as_attachment=True,
        attachment_filename=file_name
    )


@campaign_manager.route('/generate_kml', methods=['POST'])
def generate_kml():
    """Generate KML file from geojson."""
    uuid = request.values.get('uuid', None)
    campaign_name = request.values.get('campaign_name', None)
    campaign = Campaign(uuid)

    # Get json for each type.
    types = campaign.get_s3_types()
    if types is None:
        return Response(json.dumps({'error': 'types not found'}), 400)

    data = []
    for t in types:
        data.append(campaign.get_type_geojsons(t))

    if len(data) == 0:
        return Response(json.dumps({'error': 'Data not found'}), 400)

    features = [i['features'] for sublist in data for i in sublist]

    # for each type, we need to get geojson.
    kml = Kml(name=campaign_name)

    file_name = hashlib.md5(
        uuid.encode('utf-8') +
        '{:%m-%d-%Y}'.format(datetime.today()).encode('utf-8')
    ).hexdigest() + '.kml'

    file_path = os.path.join(config.CACHE_DIR, file_name)

    # For now, let's work only with points.
    # TODO: include polygons in the kml file.
    features = [[f for f in sublist if f['geometry']['type'] == 'Point']
        for sublist in features]
    features = [item for sublist in features for item in sublist]

    for feature in features:
        tags = feature['properties']['tags']
        extended_data = ExtendedData()
        kml_name = ''

        if 'name' in tags.keys():
            kml_name = tags['name']
        elif 'amenity' in tags.keys():
            kml_name = tags['amenity']

        [extended_data.newdata(k, escape(v))
            for k, v in tags.items() if k != 'name']
        kml.newpoint(
            name=kml_name,
            extendeddata=extended_data,
            coords=[
                (
                    feature['geometry']['coordinates'][0],
                    feature['geometry']['coordinates'][1]
                )
            ]
        )
    kml.save(path=file_path)
    if kml:
        # Save file into client storage device.
        return Response(json.dumps({'file_name': file_name}))


@campaign_manager.route('/download_kml/<uuid>/<file_name>')
def download_kml(uuid, file_name):
    """Download campaign as a kml file"""
    campaign = Campaign.get(uuid)

    file_path = os.path.join(
        config.CACHE_DIR,
        file_name
    )

    campaign_file_name = campaign.name + '.kml'

    if not os.path.exists(file_path):
        abort(404)

    return send_file(
        file_path,
        as_attachment=True,
        attachment_filename=campaign_file_name
    )


def get_selected_functions():
    """ Get selected function for form
    """
    functions = [
        insights_function for insights_function in [
            m[0] for m in inspect.getmembers(
                insights_functions, inspect.isclass)
            ]
        ]

    funct_dict = {}
    for insight_function in functions:
        SelectedFunction = getattr(
            insights_functions, insight_function)
        selected_function = SelectedFunction(None)

        function_name = selected_function.name()
        function_dict = {}
        function_dict['name'] = function_name
        function_dict['need_feature'] = \
            ('%s' % selected_function.need_feature).lower()
        function_dict['need_required_attributes'] = \
            ('%s' % selected_function.need_required_attributes).lower()

        funct_dict[insight_function] = function_dict
    return funct_dict


def valid_map_list():
    """List for valid maps."""

    valid_map = ({
        'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png':
            'OpenStreetMap</a> and contributors, under an '
            '<a href="http://www.openstreetmap.org/copyright" '
            'target="_parent">open license</a>',
        'https://{s}.tile.openstreetmap.de/tiles/osmde/{z}/{x}/{y}.png':
            '&copy; <a href="http://www.openstreetmap.org/copyright">'
            'OpenStreetMap</a>',
        'https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png':
            '&copy; Openstreetmap France | &copy; <a href='
            '"http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png':
            '&copy; <a href="http://www.openstreetmap.org/copyright">'
            'OpenStreetMap</a>, Tiles courtesy of '
            '<a href="http://hot.openstreetmap.org/" target="_blank">'
            'Humanitarian OpenStreetMap Team</a>',
        'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png':
            'Map data: &copy; <a href="http://www.openstreetmap.org/'
            'copyright">OpenStreetMap</a>, '
            '<a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: '
            '&copy; <a href="https://opentopomap.org">OpenTopoMap</a> '
            '(<a href="https://creativecommons.org/licenses/by-sa/3.0/">'
            'CC-BY-SA</a>)',
        'https://{s}.tile.openstreetmap.se/hydda/full/{z}/{x}/{y}.png':
            'Tiles courtesy of <a href="http://openstreetmap.se/" target='
            '"_blank">OpenStreetMap Sweden</a> &mdash; Map data &copy; <a href'
            '="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        'https://{s}.tile.openstreetmap.se/hydda/base/{z}/{x}/{y}.png':
            'Tiles courtesy of <a href="http://openstreetmap.se/" target='
            '"_blank">OpenStreetMap Sweden</a> &mdash; Map data &copy; <a href'
            '="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        'https://server.arcgisonline.com/ArcGIS/rest/services/'
        'World_Street_Map/MapServer/tile/{z}/{y}/{x}':
            'Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, '
            'Intermap, iPC, NRCAN, Esri Japan, METI, Esri China (Hong Kong), '
            'Esri (Thailand), TomTom, 2012',
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/'
        'MapServer/tile/{z}/{y}/{x}':
            'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap'
            ', iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, '
            'Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), '
            'and the GIS User Community',
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/'
        'MapServer/tile/{z}/{y}/{x}':
            'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX,'
            ' GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS '
            'User Community',
        'https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png':
            'Wikimedia maps beta | Map data &copy; <a href="http:'
            '//openstreetmap.org/copyright">OpenStreetMap contributors</a>',
        'https://maps.wikimedia.org/osm/{z}/{x}/{y}.png':
            'Wikimedia maps beta | Map data &copy; <a href="http:'
            '//openstreetmap.org/copyright">OpenStreetMap contributors</a>',
        'https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/'
        '{z}/{x}/{y}.png':
            '&copy; <a href="http://www.openstreetmap.org/copyright">'
            'OpenStreetMap</a> &copy; <a href="https://carto.com/attribution">'
            'CARTO</a>',
        'http://{s}.aerial.openstreetmap.org.za/ngi-aerial/{z}/{x}/{y}.jpg':
            'Tiles &copy; <a href="http://www.ngi.gov.za/">CD:NGI Aerial</a>',
        'https://api.mapbox.com/styles/v1/hot/cj7hdldfv4d2e2qp37cm09tl8/tiles/'
        '256/{z}/{x}/{y}':
            'OpenStreetMap</a> and contributors, under an '
            '<a href="http://www.openstreetmap.org/copyright" '
            'target="_parent">open license</a>',
    })
    return valid_map


def find_attribution(map_url):
    """Find map attribution."""

    _valid_map = valid_map_list()
    try:
        # map_url is not valid
        return _valid_map[map_url]
    except:
        return ""


@campaign_manager.route('/create', methods=['GET', 'POST'])
def create_campaign():
    import uuid
    from flask import url_for, redirect
    from campaign_manager.forms.campaign import CampaignForm
    from campaign_manager.models.campaign import Campaign
    """Get campaign details.
    """

    form = CampaignForm(request.form)
    if form.validate_on_submit():
        data = form.data
        data.pop('csrf_token')
        data.pop('submit')
        data.pop('types_options')

        data['uuid'] = uuid.uuid4().hex

        Campaign.create(data, form.uploader.data)
        Campaign.compute(data["uuid"])
        campaign = Campaign(data['uuid'])
        campaign.save()
        campaign.save_to_user_campaigns(data['user_id'],
            data['uuid'],
            Permission.ADMIN.name
        )

        return redirect(
            url_for(
                'campaign_manager.get_campaign',
                uuid=data['uuid'])
        )

    context = dict(
        oauth_consumer_key=OAUTH_CONSUMER_KEY,
        oauth_secret=OAUTH_SECRET,
        map_provider=map_provider()
    )
    context['url'] = '/create'
    context['action'] = 'create'
    context['functions'] = get_selected_functions()
    context['title'] = 'Create Campaign'
    context['maximum_area_size'] = MAX_AREA_SIZE
    context['uuid'] = uuid.uuid4().hex
    context['types'] = {}
    context['link_to_omk'] = False
    context['feature_templates'] = get_types()
    try:
        context['types'] = json.dumps(
            get_types()).replace('True', 'true').replace('False', 'false')
    except ValueError:
        pass
    return render_template(
        'create_campaign.html', form=form, **context)


@campaign_manager.route('/edit/<uuid>', methods=['GET', 'POST'])
def edit_campaign(uuid):
    import datetime
    from flask import url_for, redirect
    from campaign_manager.forms.campaign import CampaignForm
    from campaign_manager.models.campaign import Campaign
    """Get campaign details.
    """
    try:
        campaign = Campaign.get(uuid)
        context = campaign.to_dict()

        if request.method == 'GET':
            form = CampaignForm()
            form.name.data = campaign.name
            form.campaign_managers.data = parse_json_string(
                campaign.campaign_managers)
            form.campaign_viewers.data = parse_json_string(
                campaign.campaign_viewers)
            form.campaign_contributors.data = parse_json_string(
                campaign.campaign_contributors)
            form.remote_projects.data = campaign.remote_projects
            form.types.data = campaign.types
            form.description.data = campaign.description
            form.geometry.data = json.dumps(campaign.geometry)
            form.map_type.data = campaign.map_type
            form.selected_functions.data = json.dumps(
                campaign.selected_functions)
            form.start_date.data = datetime.datetime.strptime(
                campaign.start_date, '%Y-%m-%d')
            if campaign.end_date:
                form.end_date.data = datetime.datetime.strptime(
                    campaign.end_date, '%Y-%m-%d')
        else:
            form = CampaignForm(request.form)
            if form.validate_on_submit():
                data = form.data
                data.pop('types_options')
                data.pop('csrf_token')
                data.pop('submit')
                campaign.update_data(data, form.uploader.data)
                Campaign.compute(campaign.uuid)

                return redirect(
                    url_for('campaign_manager.get_campaign',
                            uuid=campaign.uuid)
                )
    except Campaign.DoesNotExist:
        return Response('Campaign not found')
    context['oauth_consumer_key'] = OAUTH_CONSUMER_KEY
    context['oauth_secret'] = OAUTH_SECRET
    context['map_provider'] = map_provider()
    context['url'] = '/edit/%s' % uuid
    context['action'] = 'edit'
    context['functions'] = get_selected_functions()
    context['title'] = 'Edit Campaign'
    context['maximum_area_size'] = MAX_AREA_SIZE
    context['uuid'] = uuid
    context['types'] = {}
    context['campaign_creator'] = campaign.campaign_creator
    context['link_to_omk'] = campaign.link_to_omk
    context['feature_templates'] = get_types()
    try:
        context['types'] = json.dumps(
            get_types()).replace('True', 'true').replace('False', 'false')
    except ValueError:
        pass
    return render_template(
        'create_campaign.html', form=form, **context)


@campaign_manager.route('/submit_campaign_data_to_json', methods=['POST'])
def submit_campaign_data_to_json():
    import uuid
    from campaign_manager.forms.campaign import CampaignForm
    from campaign_manager.models.campaign import Campaign
    """Get campaign details.
    """

    form = CampaignForm(request.form)
    if form.validate_on_submit():
        try:
            data = form.data
            data.pop('csrf_token')
            data.pop('submit')
            data.pop('types_options')

            data['uuid'] = uuid.uuid4().hex
            campaign_data = Campaign.parse_campaign_data(
                    data,
                    form.uploader.data)
            return Response(Campaign.serialize(campaign_data))
        except Exception as e:
            print(e)
    else:
        return abort(500)


@campaign_manager.route('/osm_auth')
def landing_auth():
    """Redirect page used for OSM login
    """
    return render_template('osm_auth.html')


@campaign_manager.route('/search-remote')
def search_remote():
    """Search remote projects from tasking-manager api."""
    page = request.args.get('page')
    search_text = request.args.get('textSearch', None)
    mapper_level = request.args.get('mapperLevel', None)
    mapping_types = request.args.get('mappingTypes', None)
    organisation_tag = request.args.get('organisationTag', None)
    campaign_tag = request.args.get('campaignTag', None)

    data = TaskingManagerProvider().search_project(
        page=page,
        search_text=search_text,
        mapper_level=mapper_level,
        mapping_types=mapping_types,
        organisation_tag=organisation_tag,
        campaign_tag=campaign_tag
    )
    return Response(data)


@campaign_manager.route('/project-detail')
def project_detail():
    """Search remote projects from tasking-manager api."""
    project_id = request.args.get('projectId')

    data = TaskingManagerProvider().project_detail(
        project_id=project_id,
    )
    return Response(data)


if __name__ == '__main__':
    if Config.DEBUG:
        campaign_manager.debug = True
        # set up flask to serve static content
        campaign_manager.add_url_rule(
            '/<path:path>',
            'static_file',
            static_file)
    else:
        LOGGER.info('Running in production mode')
    campaign_manager.run()


@campaign_manager.route('/403')
def forbidden():
    return forbidden_page(None)


@campaign_manager.route('/thumbnail/<image>')
def thumbnail(image):
    map_image = os.path.join(Campaign.get_thumbnail_folder(), image)
    if not os.path.exists(map_image):
        return send_file('./campaign_manager/static/img/no_map.png')
    return send_file(map_image)


@campaign_manager.route('/surveys/<survey_name>')
def survey_data(survey_name):
    survey = Survey.find_by_name(survey_name)
    return json.dumps(
        survey.data).replace('True', 'true').replace('False', 'false')


def not_found_page(error):
    context = dict(
        oauth_consumer_key=OAUTH_CONSUMER_KEY,
        oauth_secret=OAUTH_SECRET
    )
    return render_template(
        '404.html', **context)


def forbidden_page(error):
    context = dict(
        oauth_consumer_key=OAUTH_CONSUMER_KEY,
        oauth_secret=OAUTH_SECRET
    )
    return render_template(
        '403.html', **context)
