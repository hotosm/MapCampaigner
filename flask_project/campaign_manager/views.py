import json
import inspect
import os
import shapefile
import shutil
from datetime import datetime
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup
from flask import request, render_template, Response

from app_config import Config
from campaign_manager import campaign_manager
from campaign_manager.models.campaign import Campaign
from reporter import LOGGER
from reporter.static_files import static_file
from campaign_manager.utilities import module_path, temporary_folder
import campaign_manager.insights_functions as insights_functions
from campaign_manager.insights_functions._abstract_insights_function import (
    AbstractInsightsFunction
)

from urllib import request as urllibrequest


try:
    from secret import OAUTH_CONSUMER_KEY, OAUTH_SECRET
except ImportError:
    OAUTH_CONSUMER_KEY = ''
    OAUTH_SECRET = ''

MAX_AREA_SIZE = 320000000


@campaign_manager.route('/')
def home():
    """Home page view.

    On this page a summary campaign manager view will shown.
    """

    context = dict(
        oauth_consumer_key=OAUTH_CONSUMER_KEY,
        oauth_secret=OAUTH_SECRET
    )

    # noinspection PyUnresolvedReferences
    return render_template('index.html', **context)


@campaign_manager.route('/all')
def home_all():
    """Home page view.

    On this page a summary campaign manager view will shown with all campaigns.
    """

    context = dict(
        oauth_consumer_key=OAUTH_CONSUMER_KEY,
        oauth_secret=OAUTH_SECRET,
        all=True
    )

    # noinspection PyUnresolvedReferences
    return render_template('index.html', **context)


@campaign_manager.route('/tags/<tag>')
def campaigns_with_tag(tag):
    """Home page view with tag.

    On this page a summary campaign manager view will shown.
    """

    context = dict(
        oauth_consumer_key=OAUTH_CONSUMER_KEY,
        oauth_secret=OAUTH_SECRET,
        tag=tag
    )

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


@campaign_manager.route('/campaign/<uuid>/<insight_function_id>')
def get_campaign_insight_function_data(uuid, insight_function_id):
    from campaign_manager.models.campaign import Campaign
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
        return Response('Campaign not found')


def check_geojson_is_polygon(geojson):
    """Checking geojson is polygon"""
    types = ["Polygon", "MultiPolygon"]
    for feature in geojson['features']:
        if feature['geometry']['type'] not in types:
            return False
    return True


@campaign_manager.route('/campaign/<uuid>/boundary-upload-success')
def campaign_boundary_upload_chunk_success(uuid):
    """Upload chunk handle success.
    """
    from campaign_manager.models.campaign import Campaign
    from campaign_manager.data_providers.shapefile_provider import \
        ShapefileProvider
    # validate coverage
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
        return Response('Campaign not found')


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
        return Response('Campaign not found')


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
            module_path(),
            'campaigns_data',
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
        return Response('Campaign not found')


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
        return Response('Campaign not found')


@campaign_manager.route('/campaign/<uuid>/<insight_function_id>/metadata')
def get_campaign_insight_function_data_metadata(uuid, insight_function_id):
    from campaign_manager.models.campaign import Campaign
    """Get campaign details.
    """
    try:
        campaign = Campaign.get(uuid)
        data = campaign.insights_function_data_metadata(insight_function_id)
        return Response(json.dumps(data))
    except Campaign.DoesNotExist:
        return Response('Campaign not found')


@campaign_manager.route('/campaign/<uuid>')
def get_campaign(uuid):
    from campaign_manager.models.campaign import Campaign
    """Get campaign details.
    """
    try:
        campaign = Campaign.get(uuid)
        context = campaign.to_dict()
        context['oauth_consumer_key'] = OAUTH_CONSUMER_KEY
        context['oauth_secret'] = OAUTH_SECRET
        context['geometry'] = json.dumps(campaign.geometry)
        context['campaigns'] = Campaign.all()
        context['selected_functions'] = \
            campaign.get_selected_functions_in_string()

        # Calculate remaining day
        try:
            current = datetime.now()
            end_date = datetime.strptime(campaign.end_date, '%Y-%m-%d')
            remaining = end_date - current
            context['remaining_days'] = remaining.days if \
                remaining.days > 0 else 0
        except TypeError:
            context['remaining_days'] = '-'

        # Start date
        try:
            start_date = datetime.strptime(campaign.start_date, '%Y-%m-%d')
            context['start_date_date'] = start_date.strftime('%d %b')
            context['start_date_year'] = start_date.strftime('%Y')
        except TypeError:
            context['start_date_date'] = '-'
            context['start_date_year'] = '-'

        # End date
        try:
            start_date = datetime.strptime(campaign.end_date, '%Y-%m-%d')
            context['end_date_date'] = end_date.strftime('%d %b')
            context['end_date_year'] = end_date.strftime('%Y')
        except TypeError:
            context['end_date_date'] = '-'
            context['end_date_year'] = '-'

        # Participant
        context['participants'] = len(campaign.campaign_managers)

        return render_template(
            'campaign_detail.html', **context)
    except Campaign.DoesNotExist:
        context = dict(
            oauth_consumer_key=OAUTH_CONSUMER_KEY,
            oauth_secret=OAUTH_SECRET
        )
        return render_template(
            'campaign_not_found.html', **context)


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
        if not selected_function.feature:
            function_dict['features'] = selected_function.FEATURES
        function_dict['need_required_attributes'] = \
            ('%s' % selected_function.need_required_attributes).lower()
        function_dict['category'] = \
            selected_function.category

        funct_dict[insight_function] = function_dict
    return funct_dict


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

        data['uuid'] = uuid.uuid4().hex
        Campaign.create(data, form.uploader.data)
        return redirect(
            url_for(
                'campaign_manager.get_campaign',
                uuid=data['uuid'])
        )
    context = dict(
        oauth_consumer_key=OAUTH_CONSUMER_KEY,
        oauth_secret=OAUTH_SECRET
    )
    context['url'] = '/campaign_manager/create'
    context['action'] = 'create'
    context['campaigns'] = Campaign.all()
    context['categories'] = AbstractInsightsFunction.CATEGORIES
    context['functions'] = get_selected_functions()
    context['title'] = 'Create Campaign'
    context['maximum_area_size'] = MAX_AREA_SIZE
    context['uuid'] = uuid.uuid4().hex
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
            form.campaign_status.data = campaign.campaign_status
            form.campaign_managers.data = campaign.campaign_managers
            form.tags.data = campaign.tags
            form.description.data = campaign.description
            form.geometry.data = json.dumps(campaign.geometry)
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
                data.pop('csrf_token')
                data.pop('submit')
                campaign.update_data(data, form.uploader.data)
                return redirect(
                    url_for('campaign_manager.get_campaign',
                            uuid=campaign.uuid)
                )
    except Campaign.DoesNotExist:
        return Response('Campaign not found')
    context['oauth_consumer_key'] = OAUTH_CONSUMER_KEY
    context['oauth_secret'] = OAUTH_SECRET
    context['url'] = '/campaign_manager/edit/%s' % uuid
    context['action'] = 'edit'
    context['campaigns'] = Campaign.all()
    context['categories'] = AbstractInsightsFunction.CATEGORIES
    context['functions'] = get_selected_functions()
    context['title'] = 'Edit Campaign'
    context['maximum_area_size'] = MAX_AREA_SIZE
    context['uuid'] = uuid
    return render_template(
        'create_campaign.html', form=form, **context)


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
