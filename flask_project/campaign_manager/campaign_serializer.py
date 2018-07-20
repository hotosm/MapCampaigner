import ast
import inspect
import json

import campaign_manager.insights_functions as insights_functions

from flask_debugtoolbar_lineprofilerpanel.profile import line_profile

from app_config import Config
from campaign_manager.models.models import (
    session,
    User,
    Campaign,
    FeatureType,
    Team
)
from campaign_manager.utilities import (
    get_types,
    map_provider,
    get_allowed_managers
)


@line_profile
def campaign_data():
    """Campaign data in DB, active and all.
    :returns: campaign attributes for all the campaigns in the DB.
    :rtype: dict
    """
    session.rollback()  # Removes sqlalchemy integrity error
    all_campaigns = Campaign().get_all()
    active_campaigns_count = Campaign().get_active_count()
    geometries = []
    for campaign_obj in all_campaigns:
        geometries.append(get_campaign_geometry(campaign_obj))
    context = dict(
        map_provider=map_provider())
    context['active_campaigns_count'] = active_campaigns_count
    context['campaigns'] = all_campaigns
    context['geometries'] = geometries

    return context


@line_profile
def get_selected_functions():
    """ Get selected function for form.
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


@line_profile
def get_campaign_functions(functions):
    """Serializer for campaign functions.
    :param functions: Function model objects having insight functions for the
            campaign.
    :type functions: list
    :returns: serialized insight-functions.
    :rtype: dict
    """
    function_dict = {}
    i = 1
    for function in functions:
        key = 'function-' + str(i)
        function_dict[key] = {}
        if(function.name == "FeatureAttributeCompleteness"):
            function_name = (
                "Feature completeness for " +
                function.types.name)
        elif(function.name == "CountFeature"):
            function_name = (
                "No. of feature in group for " +
                function.types.name)
        elif(function.name == "MapperEngagement"):
            function_name = "Length of mapper engagement"
        function_dict[key]['name'] = function_name
        function_dict[key]['function'] = function.name
        function_dict[key]['feature'] = function.feature
        function_dict[key]['type'] = function.types.name
        function_dict[key]['attributes'] = {}
        for attribute in function.attributes:
            name = attribute.name
            function_dict[key]['attributes'][name] = []
            for val in attribute.value:
                function_dict[key]['attributes'][name].append(val)

        i += 1
    return function_dict


@line_profile
def get_campaign_geometry(campaign):
    """Serializer for campaign geometry.
    :param campaign: Campaign model object to extract the AOI.
    :type campaign: Object
    :returns: serialized geometry as GeoJSON.
    :rtype: dict
    """
    geomtery_dict = {}
    campaign_geometry_info = campaign.get_task_boundary()
    campaign_geometry = campaign.get_task_boundary_as_geoJSON()
    geomtery_dict['type'] = campaign_geometry_info.type_boundary
    geomtery_dict['features'] = []
    boundary = {}
    boundary['type'] = "Feature"
    boundary['properties'] = {}
    boundary['properties']['area'] = campaign_geometry_info.name
    boundary['properties']['status'] = campaign_geometry_info.status
    team_obj = session.query(Team).filter(
        Team.boundary_id == campaign_geometry_info.id
        ).first()
    boundary['properties']['team'] = team_obj.name
    boundary['geometry'] = ast.literal_eval(campaign_geometry[0])
    geomtery_dict['features'].append(boundary)
    return geomtery_dict


@line_profile
def get_campaign_types(campaign_obj):
    """Serializer for campaign feature types.
    :param campaign: Campaign model object to extract feature type for the
           campaign.
    :type campaign: Object
    :returns: serialized feature types.
    :rtype: dict
    """
    campaign_types = {}
    for feature_type in campaign_obj.feature_types:
        campaign_types[feature_type.name] = {}
        campaign_types[feature_type.name]["type"] = feature_type.name
        campaign_types[feature_type.name]["feature"] = feature_type.feature
        campaign_types[feature_type.name]["tags"] = {}
        for x in feature_type.tags:
            campaign_types[feature_type.name]['tags'][x.name] = []
    return campaign_types


@line_profile
def get_campaign_context(campaign_obj):
    """Get required context for edit/copy campaign.
    :param campaign_obj: additional parameters for edit/create view.
    :type: campaign_obj: Object
    :return: context dict of campaign attributes.
    :rtype: dict
    """
    context = {}
    context['allowed_managers'] = campaign_obj.get_managers()
    context['map_provider'] = map_provider()
    context['functions'] = get_selected_functions()
    context['action'] = 'edit'
    context['title'] = 'Edit Campaign'
    context['maximum_area_size'] = Config.MAX_AREA_SIZE
    context['uuid'] = campaign_obj.uuid
    context['types'] = {}
    context['campaign_creator'] = campaign_obj.creator.osm_user_id
    context['link_to_omk'] = campaign_obj.link_to_OpenMapKit
    try:
        context['types'] = json.dumps(
            get_types()).replace('True', 'true').replace('False', 'false')
    except ValueError:
        pass
    return context


@line_profile
def get_campaign_form(campaign_obj):
    """Get campaign form for edit/copy.
    :param campaign_obj: Campaign model object to extract information about
           campaign attributes.
    :type: campaign_obj: Object
    :return: form with campaign specific information.
    :rtype: CampaignForm object
    """
    from campaign_manager.forms.campaign import CampaignForm
    form = CampaignForm()
    form.campaign_managers.data = campaign_obj.get_managers()
    form.types.data = get_campaign_types(campaign_obj)
    form.geometry.data = json.dumps(get_campaign_geometry(campaign_obj))
    form.selected_functions.data = json.dumps(get_campaign_functions(
        campaign_obj.functions))
    form.name.data = campaign_obj.name
    form.remote_projects.data = campaign_obj.remote_projects
    form.description.data = campaign_obj.description
    form.map_type.data = campaign_obj.map_type
    form.start_date.data = campaign_obj.start_date
    if campaign_obj.end_date:
        form.end_date.data = campaign_obj.end_date
    return form


@line_profile
def get_new_campaign_context():
    """ Returns context for new campaign.
    :returns: campaign context and pre-defined parameters
    :rtype: dict
    """
    import uuid
    featureTypes = FeatureType().get_templates()
    teams = Team().get_all()
    managers = User().get_all()
    managers = [x.osm_user_id for x in managers]
    context = dict(
        map_provider=map_provider())
    context['allowed_managers'] = managers
    context['url'] = '/campaign'
    context['action'] = 'create'
    context['functions'] = get_selected_functions()
    context['title'] = 'Create Campaign'
    context['maximum_area_size'] = Config.MAX_AREA_SIZE
    context['uuid'] = uuid.uuid4().hex
    context['types'] = {}
    context['teams'] = teams
    context['link_to_omk'] = False
    try:
        context['types'] = json.dumps(
            get_types()).replace('True', 'true').replace('False', 'false')
    except ValueError:
        pass
    return context


def get_campaign_feature_types(feature_types):
    """ Serializes the campaign features to render campaign details.
    :param feature_types: List of campaign FeatureType objects.
    :type feature_types: Object
    :return: Campaign features in serialized form.
    :rtype: Dict
    """
    type_dict = {}
    i = 1
    for feature_type in feature_types:
        type_dict['type-' + str(i)] = {}
        type_dict['type-' + str(i)]['feature'] = feature_type.feature
        type_dict['type-' + str(i)]['type'] = feature_type.name
        type_dict['type-' + str(i)]['tags'] = {}
        for tag in feature_type.tags:
            type_dict['type-' + str(i)]['tags'][tag.name] = []
        i += 1
    return type_dict


def get_selected_functions_in_string(campaign_obj, functions):
    """ Get selected function in string to obtain overpass data based on
    selected campaign function.
    :param functions: Serialized campaign functions and attributes.
    :type functions: dict
    :return: Get selected function in string
    :rtype: str
    """
    for key, value in functions.items():
        try:
            SelectedFunction = getattr(
                insights_functions, value['function'])
            additional_data = {}
            if 'type' in value:
                additional_data['type'] = value['type']
            selected_function = SelectedFunction(
                campaign_obj,
                feature=value['feature'],
                required_attributes=value['attributes'],
                additional_data=additional_data)
            value['type_required'] = \
                ('%s' % selected_function.type_required).lower()
            value['manager_only'] = selected_function.manager_only
            value['name'] = selected_function.name()
        except AttributeError:
            value = None
    return json.dumps(functions).replace('None', 'null')
