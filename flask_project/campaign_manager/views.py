import inspect
import json
import os
import ast
import hashlib
import shutil
import requests
from simplekml import Kml, ExtendedData
from datetime import datetime
from flask import jsonify, flash
from flask import session as _session
from shapely import geometry as shapely_geometry

from urllib import request as urllibrequest
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup
from sqlalchemy.sql.expression import true
from flask_debugtoolbar_lineprofilerpanel.profile import line_profile
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
from campaign_manager.campaign_serializer import (
    campaign_data,
    get_campaign_functions,
    get_campaign_geometry,
    get_campaign_feature_types,
    get_selected_functions_in_string,
    get_new_campaign_context,
    get_campaign_context,
    get_campaign_form
)
from campaign_manager.models.campaign import Campaign
from campaign_manager.models.models import (
    session,
    User,
    Campaign
)
from campaign_manager.insights_functions.osmcha_changesets import \
    OsmchaChangesets

from campaign_manager.data_providers.overpass_provider import OverpassProvider
from reporter import config
from campaign_manager.utilities import (
    load_osm_document_cached
)
from reporter import LOGGER
from reporter.static_files import static_file
from campaign_manager.context_processor import inject_oauth_param


inject_oauth_param = campaign_manager.context_processor(inject_oauth_param)


@campaign_manager.route('/add_osm_user', methods=['POST'])
@line_profile
def add_osm_user():
    """Adds a new user to DB.
    :return: confirmation of new user registeration.
    :rtpye: Status code
    """
    osm_user = User().get_by_osm_id(request.json['username'])
    if osm_user is None:
        new_user = User(osm_user_id=request.json['username'], email='')
        new_user.create()
    return (
        json.dumps({'success': True}),
        200,
        {'ContentType': 'application/json'}
        )


@campaign_manager.route('/')
@line_profile
def home():
    """Home page view.
    On this page a summary campaign manager view will be shown with all active
    campaigns.
    """
    context = campaign_data()
    context['authority'] = 'Manage'
    # noinspection PyUnresolvedReferences
    return render_template('index.html', **context)


@campaign_manager.route('/all')
@line_profile
def home_all():
    """Home page view.
    On this page a summary campaign manager view will be shown
    with all campaigns.
    """
    context = campaign_data()
    context['authority'] = 'Manage'
    context['all'] = True
    # noinspection PyUnresolvedReferences
    return render_template('index.html', **context)


@campaign_manager.route('/inactive')
@line_profile
def home_inactive():
    """Home page view.
    On this page a summary campaign manager view will be shown
    with all inactive campaigns.
    """
    inactive_campaigns = Campaign().get_all_inactive()
    context = campaign_data()
    context['campaigns'] = inactive_campaigns
    context['authority'] = 'Manage'
    # noinspection PyUnresolvedReferences
    return render_template('index.html', **context)


@campaign_manager.route('/copy')
@line_profile
def copy():
    """Home page view.
    On this page a summary campaign manager view will be shown with all active
    campaigns .
    """
    context = campaign_data()
    context['authority'] = 'Copy'
    # noinspection PyUnresolvedReferences
    return render_template('index.html', **context)


def clean_argument(args):
    """Clean argument that is ImmutableMultiDict to dict
    and clean it's value
    :param args: Argument from request
    :type args: ImmutableMultiDict
    :return: clean argument
    :rtype: dict
    """
    arguments = dict(args)
    clean_arguments = {}
    for key, value in arguments.items():
        if len(value) == 1:
            value = value[0]
        clean_arguments[key] = value
    return clean_arguments


@campaign_manager.route('/check_email/<username>', methods=['GET'])
@line_profile
def check_user_email(username):
    """Checks user's email field.
    :param username: osm username provided by the OAuth.
    :type param: str
    :return: email flag confirmation.
    :rtype: str
    """
    email_flag = "registered"
    osm_user = User().get_by_osm_id(username)
    if osm_user.email == '':
        email_flag = "not registered"
    return email_flag


@campaign_manager.route('/register_email', methods=['POST'])
@line_profile
def register_user_email():
    """Adds user's email in DB.
    """
    from flask import url_for, redirect
    if request.method == "POST":
        data = request.form
        osm_user = User().get_by_osm_id(data['user'])
        updated_user_dict = dict(
            osm_user_id=data['user'],
            email=data['email_value'])
        osm_user.update(updated_user_dict)
    return redirect(
        url_for(
                'campaign_manager.home_all',
                )
            )


@campaign_manager.route('/campaign/<uuid>/<insight_function_id>')
@line_profile
def get_campaign_insight_function_data(uuid, insight_function_id):
    """Get campaign insight function data.
    """
    campaign_ui = ''
    campaign_obj = Campaign().get_by_uuid(uuid)
    functions = get_campaign_functions(campaign_obj.functions)
    additional_data = clean_argument(request.args)
    insight_function = functions[insight_function_id]
    SelectedFunction = getattr(
        insights_functions, insight_function['function'])
    additional_data['function_id'] = insight_function_id
    if 'type' in insight_function:
        additional_data['type'] = insight_function['type']
    selected_function = SelectedFunction(
        campaign_obj,
        feature=insight_function['feature'],
        required_attributes=insight_function['attributes'],
        additional_data=additional_data)
    # render UI
    context = {
        'selected_function_name': (insight_function['name'] +
                                   insight_function['type']),
        'icon': "list",
        'widget': selected_function.get_ui_html()
    }
    campaign_ui += render_template(
        'campaign_widget/insight_template.html',
        **context
    )
    return Response(campaign_ui)


@campaign_manager.route('/campaign/osmcha_errors/<uuid>')
@line_profile
def get_osmcha_errors_function(uuid):
    try:
        campaign = Campaign.get(uuid)
        rendered_html = campaign.render_insights_function(
            insight_function_id='total-osmcha-errors',
            insight_function_name='OsmchaChangesets',
            additional_data=clean_argument(request.args))
        return Response(rendered_html)
    except Campaign.DoesNotExist:
        abort(404)


@campaign_manager.route('/campaign/osmcha_errors_data/<uuid>')
@line_profile
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
@line_profile
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
            uuid)
        shapefile_file = "%s/%s.shp" % (
            folder, uuid)
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
@line_profile
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
@line_profile
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
@line_profile
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


@campaign_manager.route('/campaign/<uuid>')
@line_profile
def get_campaign(uuid):
    """Get campaign details.
    """
    context = {}
    try:
        campaign_obj = Campaign().get_by_uuid(uuid)
        context['campaign'] = campaign_obj
        context['map_provider'] = map_provider()
        functions = campaign_obj.functions
        functions = get_campaign_functions(functions)
        context['selected_functions'] = get_selected_functions_in_string(
            campaign_obj,
            functions)
        context['campaign_types'] = get_campaign_feature_types(
            campaign_obj.feature_types
            )
        context['geometry'] = get_campaign_geometry(campaign_obj)
        context['remote_projects'] = campaign_obj.remote_projects
        # Start date
        try:
            start_date = campaign_obj.start_date
            context['start_date'] = start_date
        except TypeError:
            context['start_date'] = '-'
        date = datetime.now().date()
        if campaign_obj.start_date <= date and date <= campaign_obj.end_date:
            context['current_status'] = 'running'
        else:
            context['current_status'] = 'inactive'
        # End date
        try:
            end_date = campaign_obj.end_date
            context['end_date'] = end_date
        except TypeError:
            context['end_date'] = '-'
        # Participant
        context['participants'] = campaign_obj.get_participants()
        return render_template(
            'campaign_detail.html', **context)
    except Exception as e:
        print(e)
        abort(404)


@campaign_manager.route('/participate')
@line_profile
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
@line_profile
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
@line_profile
def download_josm(uuid, file_name):
    """Download josm file."""
    campaign_obj = Campaign().get_by_uuid(uuid)
    campaign_name = campaign_obj.name + '.osm'
    file_path = os.path.join(config.CACHE_DIR, file_name)
    if not os.path.exists(file_path):
        abort(404)
    return send_file(
            file_path,
            as_attachment=True,
            attachment_filename=campaign_name)


@campaign_manager.route('/generate_kml', methods=['POST'])
@line_profile
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
@line_profile
def download_kml(uuid, file_name):
    """Download campaign as a kml file"""
    campaign_obj = Campaign().get_by_uuid(uuid)
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
        attachment_filename=campaign_file_name)


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


@campaign_manager.route('/campaign/new', methods=['GET'])
@line_profile
def create_campaign():
    """ Get form for creating new campaign """
    from campaign_manager.forms.campaign import CampaignForm
    form = CampaignForm()
    context = get_new_campaign_context()
    return render_template(
        'create_campaign.html', form=form, **context)


@campaign_manager.route('/campaign', methods=['POST'])
@line_profile
def save_new_campaign():
    """ Saves new campaign to the DB """
    import uuid
    from flask import url_for, redirect
    from campaign_manager.forms.campaign import CampaignForm
    # removes existing flash message from flask session
    _session.pop('_flashes', None)
    form = CampaignForm(request.form)
    print(form.data)
    try:
        if form.validate_on_submit() and request.method == 'POST':
            data = form.data
            data.pop('csrf_token')
            data.pop('submit')
            data.pop('types_options')
            data['uuid'] = uuid.uuid4().hex
            # create a new campaign
            campaign_creator = User().get_by_osm_id(data['uploader'])
            created_campaign = Campaign(
                name=data['name'],
                description=data['description'],
                creator_id=campaign_creator.id,
                start_date=data['start_date'],
                end_date=data['end_date'],
                create_on=datetime.now(),
                uuid=data['uuid'],
                version=2,
                map_type=data['map_type'],
                remote_projects=data['remote_projects'])
            created_campaign.create()
            created_campaign.save_feature_types(data)
            created_campaign.save_geometry(data)
            created_campaign.save_insight_functions(data)
            created_campaign.save_managers(data)
            created_campaign.create_thumbnail_image()
            return redirect(
                url_for(
                    'campaign_manager.get_campaign',
                    uuid=data['uuid'])
                )
    except Exception as e:
        session.rollback()
        flash("Unable to create campaign, Campaign Name already exsits.")
        return redirect(
            url_for(
                'campaign_manager.create_campaign')
            )


@campaign_manager.route('/copy/<uuid>', methods=['GET'])
@line_profile
def copy_campaign(uuid):
    """Gets the detail for copying campaign.
    """
    import uuid as _uuid
    from flask import url_for, redirect
    _session.pop('_flashes', None)
    try:
        campaign_obj = Campaign().get_by_uuid(uuid)
    except Exception as e:
        abort(404)
    context = get_campaign_context(campaign_obj)
    form = get_campaign_form(campaign_obj)
    form.name.data = None  # new name for the copy campaign
    context['url'] = '/copy/%s' % uuid
    context['mode'] = 'copy'
    context['campaign'] = campaign_obj
    return render_template(
        'create_campaign.html', form=form, **context)


@campaign_manager.route('/copy/<uuid>', methods=['POST'])
@line_profile
def save_copied_campaign(uuid):
    """ Creates a new object in DB for the copied campaign """
    import uuid as _uuid
    from flask import url_for, redirect
    from campaign_manager.forms.campaign import CampaignForm
    form = CampaignForm(request.form)
    try:
        if form.validate_on_submit():
            data = form.data
            data.pop('types_options')
            data.pop('csrf_token')
            data.pop('submit')
            data['new_uuid'] = _uuid.uuid4().hex
            new_creator = User().get_by_osm_id(data['uploader'])
            campaign_copy = Campaign(
                name=data['name'],
                description=data['description'],
                creator_id=new_creator.id,
                start_date=data['start_date'],
                end_date=data['end_date'],
                create_on=datetime.now(),
                uuid=data['new_uuid'],
                version=2,
                map_type=data['map_type'])
            campaign_copy.create()
            campaign_copy.save_feature_types(data)
            campaign_copy.save_geometry(data)
            campaign_copy.save_insight_functions(data)
            campaign_copy.save_managers(data)
            campaign_copy.create_thumbnail_image()
            return redirect(
                url_for(
                    'campaign_manager.get_campaign',
                    uuid=campaign_copy.uuid)
                )
    except Exception as e:
        session.rollback()
        try:
            campaign_obj = Campaign().get_by_uuid(uuid)
            context = get_campaign_context(campaign_obj)
            form = get_campaign_form(campaign_obj)
            context = get_campaign_context(campaign_obj)
            context['campaign'] = campaign_obj
            context['url'] = '/copy/%s' % uuid
            context['mode'] = 'copy'
            form.name.data = None
        except Exception as e:
            abort(404)
        flash('Campaign name already taken.')
        return render_template(
            'create_campaign.html', form=form, **context)


@campaign_manager.route('/edit/<uuid>', methods=['GET'])
@line_profile
def edit_campaign(uuid):
    from flask import url_for, redirect
    """Gets the campaign detail for edit campaign.
    """
    _session.pop('_flashes', None)
    try:
        campaign_obj = Campaign().get_by_uuid(uuid)
        context = get_campaign_context(campaign_obj)
        form = get_campaign_form(campaign_obj)
    except Exception as e:
        abort(404)
    context['campaign'] = campaign_obj
    context['url'] = '/edit/%s' % uuid
    context['mode'] = 'edit'
    return render_template(
        'create_campaign.html', form=form, **context)


@campaign_manager.route('/edit/<uuid>', methods=['POST'])
@line_profile
def save_edited_campaign(uuid):
    """ Saves the Updated campaign in DB """
    from flask import url_for, redirect
    from campaign_manager.forms.campaign import CampaignForm
    form = CampaignForm(request.form)
    campaign_obj = Campaign().get_by_uuid(uuid)
    try:
        if form.validate_on_submit():
            data = form.data
            data.pop('types_options')
            data.pop('csrf_token')
            data.pop('submit')
            updated_campaign_dict = dict(
                name=data['name'],
                description=data['description'],
                start_date=data['start_date'],
                end_date=data['end_date'])
            campaign_obj.update(updated_campaign_dict)
            campaign_obj.delete_taskboundaries()
            campaign_obj.delete_insight_functions()
            campaign_obj.delete_feature_types()
            campaign_obj.save_feature_types(data)
            campaign_obj.save_geometry(data)
            campaign_obj.save_insight_functions(data)
            campaign_obj.save_managers(data)
            campaign_obj.create_thumbnail_image()
            uuid = campaign_obj.uuid
            return redirect(
                url_for(
                    'campaign_manager.get_campaign',
                    uuid=uuid)
                )
    except Exception as e:
        session.rollback()
        context = get_campaign_context(campaign_obj)
        form = get_campaign_form(campaign_obj)
        context['campaign'] = campaign_obj
        context['url'] = '/edit/%s' % uuid
        context['mode'] = 'edit'
        message = (
            'There was a problem editing the campaign, '
            'the new name might belong to a existing campaign.')
        flash(message)
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
        whosthat_response = requests.get(whosthat_url)
        whosthat_data = json.loads(whosthat_response.text)
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
        campaign_tag=campaign_tag)
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


def not_found_page(error):
    return render_template(
        '404.html')


def forbidden_page(error):
    return render_template(
        '403.html')
