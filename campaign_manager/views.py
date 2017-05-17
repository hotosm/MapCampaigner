from flask import request, render_template, Response

from campaign_manager import campaign_manager


@campaign_manager.route('/')
def home():
    """Home page view.

    On this page a summary campaign manager view will shown.
    """
    context = dict(
        testing='hello'
    )
    # noinspection PyUnresolvedReferences
    return render_template('index.html', **context)


# -----------------------------------------------------------------
# Campaigner
# -----------------------------------------------------------------
@campaign_manager.route('/campaign/<uuid>/sidebar')
def get_campaign_sidebar(uuid):
    from campaign_manager.models.campaign import Campaign
    """Get campaign details.
    """
    try:
        campaign = Campaign.get(uuid)
        return Response(campaign.render_side_bar())
    except Campaign.DoesNotExist:
        return Response('Campaign not found')


@campaign_manager.route('/campaign/<uuid>')
def get_campaign(uuid):
    import json
    from campaign_manager.models.campaign import Campaign
    """Get campaign details.
    """
    try:
        campaign = Campaign.get(uuid)
        return Response(json.dumps(campaign.to_dict(), sort_keys=True))
    except Campaign.DoesNotExist:
        return Response('Campaign not found')


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
        Campaign.create(data, "Irwan")
        return redirect(
            url_for(
                'campaign_manager.get_campaign',
                uuid=data['uuid'])
        )

    return render_template('create_campaign_form.html', form=form)


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
            form.selected_functions.data = campaign.selected_functions
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
                campaign.update_data(data, 'Irwan')
                return redirect(
                    url_for('campaign_manager.get_campaign',
                            uuid=campaign.uuid)
                )
    except Campaign.DoesNotExist:
        return Response('Campaign not found')

    return render_template(
        'edit_campaign_form.html', form=form, context=context)
