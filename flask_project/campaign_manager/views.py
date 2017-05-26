import json
import inspect
import os
from datetime import datetime
from flask import request, render_template, Response

from app_config import Config
from campaign_manager import campaign_manager
from campaign_manager.models.campaign import Campaign
from reporter import LOGGER
from reporter.static_files import static_file
from campaign_manager.utilities import module_path
import campaign_manager.selected_functions as selected_functions
from campaign_manager.selected_functions._abstract_insights_function import (
    AbstractInsightsFunction
)

try:
    from secret import OAUTH_CONSUMER_KEY, OAUTH_SECRET
except ImportError:
    OAUTH_CONSUMER_KEY = ''
    OAUTH_SECRET = ''


@campaign_manager.route('/')
def home():
    """Home page view.

    On this page a summary campaign manager view will shown.
    """
    context = dict(
        oauth_consumer_key=OAUTH_CONSUMER_KEY,
        oauth_secret=OAUTH_SECRET
    )
    context['campaigns'] = Campaign.all()
    # noinspection PyUnresolvedReferences
    return render_template('index.html', **context)


@campaign_manager.route('/tags/<tag>')
def campaigns_with_tag(tag):
    """Home page view with tag.

    On this page a summary campaign manager view will shown.
    """
    context = dict(
        oauth_consumer_key=OAUTH_CONSUMER_KEY,
        oauth_secret=OAUTH_SECRET
    )
    context['campaigns'] = Campaign.all({
        'tags': tag
    })
    # noinspection PyUnresolvedReferences
    return render_template('index.html', **context)


@campaign_manager.route('/campaign/<uuid>/<insight_function_id>')
def get_campaign_insight_function_data(uuid, insight_function_id):
    from campaign_manager.models.campaign import Campaign
    """Get campaign insight function data.
    """
    try:
        campaign = Campaign.get(uuid)
        rendered_html = campaign.render_insights_function(insight_function_id)
        return Response(rendered_html)
    except Campaign.DoesNotExist:
        return Response('Campaign not found')


@campaign_manager.route('/campaign/<uuid>/coverage-upload-chunk', methods=['POST'])
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
    except Campaign.DoesNotExist:
        return Response('Campaign not found')


@campaign_manager.route('/campaign/<uuid>/coverage-upload-success')
def campaign_coverage_upload_chunk_success(uuid):
    from campaign_manager.models.campaign import Campaign
    """Upload chunk handle success.
    """
    try:
        campaign = Campaign.get(uuid)
        campaign.coverage = {
            'last_uploader': request.args.get('uploader', ''),
            'last_uploaded': datetime.now().strftime('%Y-%m-%d')

        }
        coverage_uploader = request.args.get('uploader', '')
        campaign.save(coverage_uploader)
        return Response(json.dumps(campaign.to_dict()))
    except Campaign.DoesNotExist:
        return Response('Campaign not found')


@campaign_manager.route('/campaign/<uuid>/coverage')
def get_campaign_coverage(uuid):
    from campaign_manager.models.campaign import Campaign
    """Get campaign details.
    """
    try:
        campaign = Campaign.get(uuid)
        return Response(json.dumps(campaign.get_coverage()))
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
        context['selected_functions'] = campaign.get_selected_functions_in_string()

        # Calculate remaining day
        try:
            current = datetime.now()
            end_date = datetime.strptime(campaign.end_date, '%Y-%m-%d')
            remaining = end_date - current
            context['remaining_days'] = remaining.days if remaining.days > 0 else 0
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
                selected_functions, inspect.isclass)
            ]
        ]

    funct_dict = {}
    for insight_function in functions:
        SelectedFunction = getattr(
            selected_functions, insight_function)
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
    context['action'] = '/campaign_manager/create'
    context['campaigns'] = Campaign.all()
    context['categories'] = AbstractInsightsFunction.CATEGORIES
    context['functions'] = get_selected_functions()
    context['title'] = 'Create Campaign'
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
            form.selected_functions.data = json.dumps(campaign.selected_functions)
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
    context['action'] = '/campaign_manager/edit/%s' % uuid
    context['campaigns'] = Campaign.all()
    context['categories'] = AbstractInsightsFunction.CATEGORIES
    context['functions'] = get_selected_functions()
    context['title'] = 'Edit Campaign'
    return render_template(
        'create_campaign.html', form=form, **context)


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
        campaign_manager.add_url_rule('/<path:path>', 'static_file', static_file)
    else:
        LOGGER.info('Running in production mode')
    campaign_manager.run()
