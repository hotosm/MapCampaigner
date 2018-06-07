import inspect
import json
import os
import ast
import hashlib
import shutil
from simplekml import Kml, ExtendedData
from datetime import datetime
from flask import jsonify
from shapely import geometry as shapely_geometry

from urllib import request as urllibrequest
from urllib.error import HTTPError, URLError

from bs4 import BeautifulSoup
from sqlalchemy import and_, or_
from sqlalchemy.sql.expression import true
from sqlalchemy.orm import sessionmaker
from geoalchemy2.shape import from_shape
from shapely.geometry import asShape
from flask import (
    request,
    render_template,
    Response,
    abort,
    send_file,
    send_from_directory,
    jsonify
)

from app_config import Config
from campaign_manager import campaign_manager
from campaign_manager.utilities import (
    get_types,
    map_provider,
    get_allowed_managers
)
import campaign_manager.insights_functions as insights_functions
from campaign_manager.insights_functions._abstract_insights_function import (
    AbstractInsightsFunction
)
from campaign_manager.utilities import temporary_folder
from campaign_manager.data_providers.tasking_manager import \
    TaskingManagerProvider
from campaign_manager.api import CampaignNearestList, CampaignList
from campaign_manager.models.campaign import Campaign
from campaign_manager.models.models import *
from campaign_manager.insights_functions.osmcha_changesets import \
    OsmchaChangesets

from campaign_manager.data_providers.overpass_provider import OverpassProvider
from reporter import config
from campaign_manager.utilities import (
    load_osm_document_cached
)
from reporter import LOGGER
from reporter.static_files import static_file

try:
    from secret import OAUTH_CONSUMER_KEY, OAUTH_SECRET
except ImportError:
    OAUTH_CONSUMER_KEY = ''
    OAUTH_SECRET = ''

MAX_AREA_SIZE = 320000000

# create session for Database Queries
Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
session = Session()
session.rollback()


@campaign_manager.route('/add_osm_user/<username>', methods=['GET', 'POST'])
def add_osm_user(username):
    user = session.query(User).filter(User.osm_user_id == username).all()
    # add to db if user is new.
    if len(user) == 0:
        new_user = User(osm_user_id=username, email='')
        session.add(new_user)
        session.commit()
    return "user is here"


@campaign_manager.route('/')
def home():
    """Home page view.
    On this page a summary campaign manager view will be shown with all active
    campaigns .
    """
    date = datetime.now().date()
    campaigns = session.query(Campaign).all()
    active_campaigns = session.query(Campaign).filter(
                    and_(Campaign.start_date <= date,
                         date <= Campaign.end_date)).all()
    geometry = []
    for campaign in campaigns:
        geometry.append(get_campaign_geometry(campaign))

    context = dict(
        oauth_consumer_key=OAUTH_CONSUMER_KEY,
        oauth_secret=OAUTH_SECRET,
        map_provider=map_provider()
    )
    context['active_campaigns'] = len(active_campaigns)
    context['campaigns'] = campaigns
    context['geometry'] = geometry
    context['authority'] = 'Manage'
    # noinspection PyUnresolvedReferences
    return render_template('index.html', **context)


@campaign_manager.route('/all')
def home_all():
    """Home page view.
    On this page a summary campaign manager view will be shown
    with all campaigns.
    """
    date = datetime.now().date()
    campaigns = session.query(Campaign).all()
    active_campaigns = session.query(Campaign).filter(
                    and_(Campaign.start_date <= date,
                         date <= Campaign.end_date)).all()
    geometry = []
    for campaign in campaigns:
        geometry.append(get_campaign_geometry(campaign))

    context = dict(
        oauth_consumer_key=OAUTH_CONSUMER_KEY,
        oauth_secret=OAUTH_SECRET,
        all=True,
        map_provider=map_provider()
    )

    context['active_campaigns'] = len(active_campaigns)
    context['campaigns'] = campaigns
    context['geometry'] = geometry
    context['authority'] = 'Manage'
    # noinspection PyUnresolvedReferences
    return render_template('index.html', **context)


@campaign_manager.route('/inactive')
def home_inactive():
    """Home page view.
    On this page a summary campaign manager view will be shown
    with all inactive campaigns.
    """
    date = datetime.now().date()
    active_campaigns = session.query(Campaign).filter(
                    and_(Campaign.start_date <= date,
                         date <= Campaign.end_date)).all()
    inactive_campaigns = session.query(Campaign).filter(
                    or_(Campaign.start_date >= date,
                        date >= Campaign.end_date)).all()
    geometry = []
    for campaign in inactive_campaigns:
        geometry.append(get_campaign_geometry(campaign))
    context = dict(
        oauth_consumer_key=OAUTH_CONSUMER_KEY,
        oauth_secret=OAUTH_SECRET,
        map_provider=map_provider()
    )

    context['active_campaigns'] = len(active_campaigns)
    context['campaigns'] = inactive_campaigns
    context['geometry'] = geometry
    context['authority'] = 'Manage'
    # noinspection PyUnresolvedReferences
    return render_template('index.html', **context)


@campaign_manager.route('/copy')
def copy_campaign():
    """Home page view.
    On this page a summary campaign manager view will be shown with all active
    campaigns .
    """
    date = datetime.now().date()
    campaigns = session.query(Campaign).all()
    active_campaigns = session.query(Campaign).filter(
                    and_(Campaign.start_date <= date,
                         date <= Campaign.end_date)).all()
    geometry = []
    for campaign in campaigns:
        geometry.append(get_campaign_geometry(campaign))
    context = dict(
        oauth_consumer_key=OAUTH_CONSUMER_KEY,
        oauth_secret=OAUTH_SECRET,
        map_provider=map_provider()
    )

    context['active_campaigns'] = len(active_campaigns)
    context['campaigns'] = campaigns
    context['geometry'] = geometry
    context['authority'] = 'Copy'
    # noinspection PyUnresolvedReferences
    return render_template('index.html', **context)


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


@campaign_manager.route('/check_email/<user>', methods=['GET'])
def check_user_email(user):
    email_flag = "registered"
    user = session.query(User).filter(User.osm_user_id == user).first()
    if user.email == '':
        email_flag = "not registered"
    return email_flag


@campaign_manager.route('/register_email', methods=['POST'])
def register_user_email():
    from flask import url_for, redirect
    print(request.form)
    if request.method == "POST":
        data = request.form
        user = session.query(User).filter(User.osm_user_id ==
                                          data['user']).first()
        user.email = data['email_value']
        session.commit()
    return redirect(
        url_for(
                'campaign_manager.home_all',
                )
            )


@campaign_manager.route('/campaign/<uuid>/<insight_function_id>')
def get_campaign_insight_function_data(uuid, insight_function_id):
    """Get campaign insight function data.
    """
    try:
        campaign = Campaign.get(uuid)
        rendered_html = campaign.render_insights_function(
            insight_function_id,
            additional_data=clean_argument(request.args)
        )
        return Response(rendered_html)
    except Campaign.DoesNotExist:
        abort(404)


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


@campaign_manager.route('/campaign/<uuid>/coverage-upload-success')
def campaign_coverage_upload_chunk_success(uuid):
    """Upload chunk handle success.
    """
    from campaign_manager.models.campaign import Campaign
    from campaign_manager.insights_functions.upload_coverage import (
        UploadCoverage
    )
    # validate coverage
    try:
        campaign = Campaign.get(uuid)
        coverage_function = UploadCoverage(campaign)
        coverage = coverage_function.get_function_raw_data()
        if not coverage:
            coverage_function.delete_coverage_files()
            return Response(json.dumps({
                'success': False,
                'reason': 'Shapefile is not valid.'
            }))
        if not check_geojson_is_polygon(coverage):
            coverage_function.delete_coverage_files()
            return Response(json.dumps({
                'success': False,
                'reason': 'It is not in polygon/multipolygon type.'
            }))

        try:
            coverage['features'][0]['properties']['date']
        except KeyError:
            coverage_function.delete_coverage_files()
            return Response(json.dumps({
                'success': False,
                'reason': 'Needs date attribute in shapefile.'
            }))

        campaign.coverage = {
            'last_uploader': request.args.get('uploader', ''),
            'last_uploaded': datetime.now().strftime('%Y-%m-%d'),
            'geojson': coverage

        }
        coverage_uploader = request.args.get('uploader', '')
        campaign.save(coverage_uploader)
        return Response(json.dumps({
            'success': True,
            'data': campaign.coverage,
            'files': coverage_function.get_coverage_files()
        }))
    except Campaign.DoesNotExist:
        abort(404)


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


def get_campaign_function(functions):
    function_dict = {}
    i = 1
    for function in functions:
        function_dict['function-' + str(i)] = {}
        function_dict['function-' + str(i)]['name'] = "Name of Function"
        function_dict['function-' + str(i)]['function'] = function.name
        function_dict['function-' + str(i)]['feature'] = function.feature
        function_dict['function-' + str(i)]['type'] = function.types.name
        function_dict['function-' + str(i)]['attributes'] = {}
        for tag in function.types.attributes:
            tag_name = tag.attribute_name
            function_dict['function-' + str(i)]['attributes'][tag_name] = []
        i += 1
    return function_dict


def get_campaign_geometry(campaign):
    geomtery_dict = {}
    campaign_geometry_info = session.query(TaskBoundary).filter(
        TaskBoundary.campaign_id == campaign.id).first()
    campaign_geometry = session.query(TaskBoundary.coordinates.ST_AsGeoJSON()
                                      ).filter(TaskBoundary.campaign_id ==
                                               campaign.id).first()
    geomtery_dict['type'] = campaign_geometry_info.type_boundary
    geomtery_dict['features'] = []
    boundary = {}
    boundary['type'] = "Feature"
    boundary['properties'] = {}
    boundary['properties']['area'] = campaign_geometry_info.name
    boundary['properties']['status'] = campaign_geometry_info.status
    team_obj = session.query(Team).filter(Team.boundary_id ==
                                          campaign_geometry_info.id).first()
    boundary['properties']['team'] = team_obj.name
    boundary['geometry'] = ast.literal_eval(campaign_geometry[0])
    geomtery_dict['features'].append(boundary)
    return geomtery_dict


@campaign_manager.route('/campaign/<uuid>')
def get_campaign(uuid):

    """Get campaign details.
    """
    context = {}
    try:
        campaign = session.query(Campaign).filter(Campaign.uuid == uuid
                                                  ).first()
        context['campaign'] = campaign
        context['oauth_consumer_key'] = OAUTH_CONSUMER_KEY
        context['oauth_secret'] = OAUTH_SECRET
        context['map_provider'] = map_provider()
        functions = campaign.functions
        context['selected_functions'] = get_campaign_function(functions)
        # load campaign geomerty
        context['geometry'] = get_campaign_geometry(campaign)

        # Start date
        try:
            start_date = campaign.start_date
            context['start_date'] = start_date
        except TypeError:
            context['start_date'] = '-'
        date = datetime.now().date()
        if campaign.start_date <= date and date <= campaign.end_date:
            context['current_status'] = 'running'
        # End date
        try:
            end_date = campaign.end_date
            context['end_date'] = end_date
        except TypeError:
            context['end_date'] = end_date
        # Participant
        context['participants'] = len(campaign.users)
        return render_template(
            'campaign_detail.html', **context)
    except Campaign.DoesNotExist:
        abort(404)


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


@campaign_manager.route('/generate_josm', methods=['POST'])
def generate_josm():
    """Get overpass xml data from ids store it to temporary folder."""
    error_features = request.values.get('error_features', None)
    if not error_features:
        abort(404)

    server_url = 'http://exports-prod.hotosm.org:6080/api/' \
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
    campaign = campaign = session.query(Campaign).filter(Campaign.uuid ==
                                                         uuid).first()
    campaign_name = campaign.name + '.osm'
    file_path = os.path.join(config.CACHE_DIR, file_name)
    if not os.path.exists(file_path):
        abort(404)
    return send_file(
            file_path,
            as_attachment=True,
            attachment_filename=campaign_name)


@campaign_manager.route('/generate_kml', methods=['POST'])
def generate_kml():
    """Generate KML file from geojson."""
    features = request.values.get('location', None)
    uuid = request.values.get('uuid', None)
    campaign_name = request.values.get('campaign_name', None)
    if not features or not uuid:
        abort(404)
    features = json.loads(features)
    kml = Kml(name=campaign_name)

    file_name = hashlib.md5(
        uuid.encode('utf-8') +
        '{:%m-%d-%Y}'.format(datetime.today()).encode('utf-8')
    ).hexdigest() + '.kml'

    file_path = os.path.join(
        config.CACHE_DIR,
        file_name
    )

    for feature in features:
        if feature['type'] == 'Point':
            kml_name = ''
            extended_data = ExtendedData()

            if 'name' in feature['tags']:
                kml_name = feature['tags']['name']
            elif 'amenity' in feature['tags']:
                kml_name = feature['tags']['amenity']

            for key, value in feature['tags'].items():
                if key != 'name':
                    extended_data.newdata(key, value)

            kml.newpoint(
                name=kml_name,
                extendeddata=extended_data,
                coords=[
                    (
                        feature['latlon'][1],
                        feature['latlon'][0]
                    )
                ]
            )

    kml.save(path=file_path)
    if kml:
        return Response(json.dumps({'file_name': file_name}))


@campaign_manager.route('/download_kml/<uuid>/<file_name>')
def download_kml(uuid, file_name):
    """Download campaign as a kml file"""
    campaign = session.query(Campaign).filter(Campaign.uuid == uuid).first()

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
    attribution = _valid_map[map_url]
    return attribution


def fillCampaignData(campaign, data):
    """
        Creates or updates the campaign object in the database
    """
    # pre-processing featureTypes and feature-attributes
    data_types = ast.literal_eval(data['types'])
    for _type in data_types:
        type_dict = data_types[_type]
        name = type_dict['type']
        feature = type_dict['feature']
        featureType = FeatureType(feature=feature, name=name)
        session.add(featureType)
        session.commit()  # commit new/modified feature type to the database
        # commit attributes for the feature to the database
        for _tag in type_dict['tags']:
            attribute = Attribute(attribute_name=_tag)
            session.add(attribute)
            session.commit()
            featureType.attributes.append(attribute)
        session.commit()
        campaign.featureTypes.append(featureType)
    session.commit()
    # pre-processing geometry to obtain campaign geometry and taskboundary
    data_geometry = ast.literal_eval(data['geometry'])
    geom = data_geometry['features'][0]['geometry']
    geom_obj = from_shape(asShape(geom), srid=4326)
    area = data_geometry['features'][0]['properties']['area']
    status = data_geometry['features'][0]['properties']['status']
    taskboundary_type = data_geometry['type']
    taskboundary = TaskBoundary(coordinates=geom_obj,
                                campaign_id=campaign.id,
                                name=area,
                                status=status,
                                type_boundary=taskboundary_type)
    session.add(taskboundary)
    session.commit()
    campaign.taskBoundaries.append(taskboundary)
    session.commit()
    team = data_geometry['features'][0]['properties']['team']
    team_obj = Team(name=team, boundary_id=taskboundary.id)
    session.add(team_obj)
    session.commit()
    # pre-processing managers to obtain campaign managers
    for manager in data['campaign_managers']:
        manager = session.query(User).filter(User.osm_user_id ==
                                             manager).first()
        campaign.users.append(manager)
    session.commit()
    # pre-processing selected_function to obtain functions for the campaign
    data_function_selected = ast.literal_eval(data['selected_functions'])
    for function in data_function_selected:
        name = data_function_selected[function]['function']
        feature = data_function_selected[function]['feature']
        selected_type = data_function_selected[function]['type']
        _type = session.query(FeatureType).filter(FeatureType.name ==
                                                  selected_type).first()
        selected_function = Function(name=name,
                                     feature=feature,
                                     type_id=_type.id)
        session.add(selected_function)
        session.commit()
        campaign.functions.append(selected_function)
    session.commit()


@campaign_manager.route('/create', methods=['GET', 'POST'])
def create_campaign():
    import uuid
    from flask import url_for, redirect
    from campaign_manager.forms.campaign import CampaignForm
    # Get all the template feature types for the campaign from the database
    featureTypes =\
        session.query(FeatureType).filter(FeatureType.is_template ==
                                          true()).all()

    # Get all the pre-registered Teams from the FieldCampaigner Database
    teams = session.query(Team).all()

    # Get managers/users registered in the
    managers = session.query(User).all()
    managers = [x.osm_user_id for x in managers]

    # If there is no managers
    if not managers:
        abort(403)

    form = CampaignForm(request.form)
    if form.validate_on_submit() and request.method == 'POST':
        data = form.data
        data.pop('csrf_token')
        data.pop('submit')
        data.pop('types_options')

        data['uuid'] = uuid.uuid4().hex

        if data['uploader'] not in managers:
            abort(403)
        campaign_creator = session.query(User).filter(User.osm_user_id ==
                                                      data['uploader']
                                                      ).first()
        created_campaign = Campaign(name=data['name'],
                                    description=data['description'],
                                    creator_id=campaign_creator.id,
                                    start_date=data['start_date'],
                                    end_date=data['end_date'],
                                    create_on=datetime.now(),
                                    uuid=data['uuid'],
                                    version=2,
                                    map_type=data['map_type'])
        session.add(created_campaign)
        session.commit()
        fillCampaignData(created_campaign, data)
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
    context['allowed_managers'] = managers
    context['url'] = '/create'
    context['action'] = 'create'
    context['functions'] = get_selected_functions()
    context['title'] = 'Create Campaign'
    context['maximum_area_size'] = MAX_AREA_SIZE
    context['uuid'] = uuid.uuid4().hex
    context['types'] = featureTypes
    context['teams'] = teams
    context['link_to_omk'] = False
    return render_template(
        'create_campaign.html', form=form, **context)


@campaign_manager.route('/edit/<mode>/<uuid>', methods=['GET', 'POST'])
def edit_campaign(mode, uuid):
    import uuid as ud
    from flask import url_for, redirect
    from campaign_manager.forms.campaign import CampaignForm
    """Get campaign details.
    """
    context = {}
    try:
        campaign = session.query(Campaign).filter(Campaign.uuid ==
                                                  uuid).first()
        context['campaign'] = campaign
        # Get managers
        managers = campaign.users
        managers = [x.osm_user_id for x in managers]
        campaign_types = {}

        # Preprocess campaign data
        for _ in campaign.featureTypes:
            campaign_types[_.name] = {}
            campaign_types[_.name]["type"] = _.name
            campaign_types[_.name]["feature"] = _.feature
            campaign_types[_.name]["tags"] = {}
            for x in _.attributes:
                campaign_types[_.name]['tags'][x.attribute_name] = []
        if request.method == 'GET':
            form = CampaignForm()
            form.name.data = campaign.name
            form.campaign_managers.data = managers
            form.remote_projects.data = campaign.remote_projects
            form.types.data = campaign_types
            form.description.data = campaign.description
            form.geometry.data = json.dumps(get_campaign_geometry(campaign))
            form.map_type.data = campaign.map_type
            form.selected_functions.data = json.dumps(get_campaign_function(
                                                        campaign.functions))
            form.start_date.data = campaign.start_date
            if campaign.end_date:
                form.end_date.data = campaign.end_date
        else:
            form = CampaignForm(request.form)
            if form.validate_on_submit():
                data = form.data
                data.pop('types_options')
                data.pop('csrf_token')
                data.pop('submit')
                # Edit Campaign
                if mode == "edit":
                    fillCampaignData(campaign, data)
                    uuid = campaign.uuid
                # Copy Existing Campaign
                elif mode == "copy":
                    data['new_uuid'] = ud.uuid4().hex
                    new_creator = \
                        session.query(User).filter(User.osm_user_id ==
                                                   data['uploader']
                                                   ).first()
                    campaign_copy = Campaign(name=data['name'],
                                             description=data['description'],
                                             creator_id=new_creator.id,
                                             start_date=data['start_date'],
                                             end_date=data['end_date'],
                                             create_on=datetime.now(),
                                             uuid=data['new_uuid'],
                                             version=2,
                                             map_type=data['map_type'])
                    session.add(campaign_copy)
                    session.commit()
                    print("this is copy")
                    fillCampaignData(campaign_copy, data)
                    uuid = campaign_copy.uuid
                return redirect(
                    url_for('campaign_manager.get_campaign',
                            uuid=uuid)
                )
    except Exception as e:
        return Response('Campaign not found')

    context['allowed_managers'] = managers
    context['oauth_consumer_key'] = OAUTH_CONSUMER_KEY
    context['oauth_secret'] = OAUTH_SECRET
    context['map_provider'] = map_provider()
    if mode == "edit":
        context['url'] = '/edit/edit/%s' % uuid
        context['mode'] = 'edit'
    elif mode == "copy":
        context['url'] = '/edit/copy/%s' % uuid
        context['mode'] = 'copy'
    context['action'] = 'edit'
    context['functions'] = get_selected_functions()
    context['title'] = 'Edit Campaign'
    context['maximum_area_size'] = MAX_AREA_SIZE
    context['uuid'] = uuid
    context['types'] = {}
    context['campaign_creator'] = campaign.creator.osm_user_id
    context['link_to_omk'] = campaign.link_to_OpenMapKit
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


@campaign_manager.route('/search_osm/<query_name>', methods=['GET'])
def get_osm_names(query_name):
    whosthat_url = 'http://whosthat.osmz.ru/whosthat.php?action=names&q=' \
                   + query_name.replace(" ", "%20")
    whosthat_data = []
    osm_usernames = []
    found_exact = False

    try:
        whosthat_response = urllibrequest.urlopen(whosthat_url)
        whosthat_data = json.loads(whosthat_response.read())
    except (HTTPError, URLError):
        print("connection error")

    for whosthat_names in whosthat_data:
        for whosthat_name in whosthat_names['names']:
            if whosthat_name.lower() == query_name:
                found_exact = True
            osm_usernames.append(whosthat_name)

    # If username not found in whosthat db, check directly to openstreetmap
    osm_response = None
    if not found_exact:
        osm_url = 'https://www.openstreetmap.org/user/' + \
                  query_name.replace(" ", "%20")
        try:
            osm_response = urllibrequest.urlopen(osm_url)
        except (HTTPError, URLError):
            print("connection error")

    if osm_response:
        osm_soup = BeautifulSoup(osm_response, 'html.parser')
        osm_title = osm_soup.find('title').string
        if query_name in osm_title:
            osm_usernames.append(query_name)

    return Response(json.dumps(osm_usernames))


@campaign_manager.route('/land')
def landing_auth():
    """OSM auth landing page.
    """
    return render_template('land.html')


@campaign_manager.route('/not-logged-in.html')
def not_logged_in():
    """Not logged in page.
    """
    return render_template('not_authenticated.html')


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


@campaign_manager.route('/about')
def about():
    return render_template('about.html')


@campaign_manager.route('/resources')
def resources():
    return render_template('resources.html')


@campaign_manager.route('/how-it-works')
def how_it_works():
    return render_template('how_it_works.html')


@campaign_manager.route('/403')
def forbidden():
    return forbidden_page(None)


@campaign_manager.route('/thumbnail/<image>')
def thumbnail(image):
    map_image = os.path.join(Campaign.get_thumbnail_folder(), image)
    if not os.path.exists(map_image):
        return send_file('./campaign_manager/static/img/no_map.png')
    return send_file(map_image)


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
