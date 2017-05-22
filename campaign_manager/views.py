import json
import inspect
from flask import request, render_template, Response
from campaign_manager import campaign_manager
from campaign_manager.models.campaign import Campaign
import campaign_manager.selected_functions as selected_functions
from  campaign_manager.selected_functions._abstract_insights_function import (
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


@campaign_manager.route('/campaign/<uuid>/<insight_function_id>')
def get_campaign_insight_function_data(uuid, insight_function_id):
    from campaign_manager.models.campaign import Campaign
    """Get campaign details.
    """
    try:
        campaign = Campaign.get(uuid)
        data = campaign.insight_function_data(insight_function_id)
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
        context['campaigns'] = Campaign.all()
        context['geometry'] = json.dumps(campaign.geometry)
        context['selected_functions'] = campaign.get_selected_functions_in_string()
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
        funct_dict[insight_function] = {}
        funct_dict[insight_function]['need_feature'] = \
            ('%s' % selected_function.need_feature).lower()
        if not selected_function.feature:
            funct_dict[insight_function]['features'] = selected_function.FEATURES
        funct_dict[insight_function]['need_required_attributes'] = \
            ('%s' % selected_function.need_required_attributes).lower()
        funct_dict[insight_function]['category'] = \
            selected_function.category
    return funct_dict


@campaign_manager.route('/campaign/create', methods=['GET', 'POST'])
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
    context['action'] = '/campaign_manager/campaign/create'
    context['campaigns'] = Campaign.all()
    context['categories'] = AbstractInsightsFunction.CATEGORIES
    context['functions'] = get_selected_functions()
    return render_template(
        'create_campaign_form.html', form=form, **context)


@campaign_manager.route('/campaign/edit/<uuid>', methods=['GET', 'POST'])
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
            form.coverage.data = campaign.coverage
            form.campaign_managers.data = campaign.campaign_managers
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
    context['action'] = '/campaign_manager/campaign/edit/%s' % uuid
    context['campaigns'] = Campaign.all()
    context['categories'] = AbstractInsightsFunction.CATEGORIES
    context['functions'] = get_selected_functions()
    return render_template(
        'create_campaign_form.html', form=form, **context)


@campaign_manager.route('/land.html')
def landing_auth():
    """OSM auth landing page.
    """
    return render_template('land.html')


@campaign_manager.route('/not-logged-in.html')
def not_logged_in():
    """Not logged in page.
    """
    return render_template('not_authenticated.html')
