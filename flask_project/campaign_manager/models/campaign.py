__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '10/05/17'

from datetime import datetime, date, timedelta
import bisect
import math
import copy
import hashlib
import requests
import shutil
import json
import os
import pygeoj
import time
import zlib

from flask import render_template
from shapely import geometry as shapely_geometry
from shapely.geometry import mapping, shape, JOIN_STYLE
from shapely.ops import cascaded_union
import numpy

from app_config import Config
import campaign_manager.insights_functions as insights_functions
from campaign_manager.models.json_model import JsonModel
from campaign_manager.git_utilities import save_with_git
from campaign_manager.utilities import (
    get_survey_json,
    parse_json_string,
    simplify_polygon
)
from campaign_manager.aws import S3Data
from enum import Enum
from os.path import join
import visvalingamwyatt as vw


USER_CAMPAIGNS = 'user_campaigns'


class Permission(Enum):
    ADMIN = 0
    MANAGER = 1
    VIEWER = 2


class Campaign(JsonModel):
    """
    Class campaign model that hold campaign information and functions.
    """
    uuid = ''
    name = ''
    campaign_creator = ''
    participants_count_per_type = {}
    total_participants_count = 0
    coverage = {}
    geometry = None
    start_date = None
    end_date = None
    campaign_managers = []
    selected_functions = []
    remote_projects = []
    types = []
    description = ''
    _content_json = None
    map_type = ''
    dashboard_settings = ''
    link_to_omk = False
    thumbnail = ''
    user_id = None

    def __init__(self, uuid=None):
        if uuid:
            self.uuid = uuid
            self.json_path = Campaign.get_json_file(uuid)
            self.geojson_path = Campaign.get_geojson_file(uuid)
            self.edited_at = S3Data().get_last_modified_date(self.json_path)
            self.parse_json_file()

    @staticmethod
    def save_to_user_campaigns(user_id, uuid, level):
        s3_obj = S3Data()

        # Validate that user file exists. If not create it.
        user_file = join(USER_CAMPAIGNS, f'{user_id}.json')
        user_campaigns = s3_obj.fetch(user_file)
        campaign = {
            'uuid': uuid,
            'permission': Permission[level].value
        }

        if len(user_campaigns) == 0:
            user_campaigns = {
                'projects': [campaign]
            }
        else:
            # Validate that campaign does not exist.
            uuids = [c['uuid'] for c in user_campaigns['projects']]
            if uuid in uuids:
                raise ValueError("Campaign already exists")
            user_campaigns['projects'].append(campaign)

        body = json.dumps(user_campaigns)
        s3_obj.create(user_file, body)

        return True

    def save(self, uploader=None, save_to_git=True):
        """Save current campaign

        :param uploader: uploader who created
        :type uploader: str
        """
        self.version += 1
        if uploader:
            self.edited_by = uploader

        # Generate map
        self.generate_static_map()

        data = self.to_dict()
        Campaign.validate(data, self.uuid)

        geometry = data['geometry']
        del data['geometry']

        # save updated campaign to json
        campaign_key = self.json_path
        campaign_body = Campaign.serialize(data)
        S3Data().create(campaign_key, campaign_body)

        geocampaign_key = self.geojson_path
        geocampaign_body = json.dumps(geometry)
        S3Data().create(geocampaign_key, geocampaign_body)

    def generate_static_map_url(self, simplify):
        """
        Generate a MapBox static map URL in production/staging.
        Generate a OpenStreetMap static map URL in development.

        :param simplify: if set to True, it will simplify the GeoJSON.
        :type simplify: boolean

        :return: HTTP URL
        :rtype: str
        """
        if 'MAPBOX_TOKEN' in os.environ:
            url = 'https://api.mapbox.com/styles/v1/hot/' \
                  'cj7hdldfv4d2e2qp37cm09tl8/static/geojson({overlay})/' \
                  'auto/{width}x{height}?' \
                  'access_token=' + os.environ['MAPBOX_TOKEN']

            if len(self.geometry['features']) > 1:
                geometry = {
                    'type': 'Feature',
                    'properties': {},
                    'geometry': mapping(self.get_union_polygons())
                }

                geometry = json.dumps(geometry, separators=(',', ':'))

            else:
                feature = self.geometry['features'][0]
                feature['properties'] = {}

                if simplify:
                    feature['geometry'] = vw.simplify_geometry(
                        feature['geometry'],
                        ratio=0.20)

                geometry = json.dumps(
                    feature,
                    separators=(',', ':'))

            url = url.format(
                overlay=geometry,
                width=512,
                height=300
            )

        else:
            polygon = self.get_union_polygons()

            url = 'http://staticmap.openstreetmap.de/staticmap.php?' \
                  'center={y},{x}&zoom=10&size=512x300&maptype=mapnik' \
                  '&markers={y},{x},lightblue'.format(
                    y=polygon.centroid.y,
                    x=polygon.centroid.x)

        return url

    def generate_static_map(self, simplify=False):
        """
        Download static map from http://staticmap.openstreetmap.de with marker,
        then save it thumbnail folder.

        :param simplify: if set to True, it will simplify the GeoJSON.
        :type simplify: boolean

        """
        url = self.generate_static_map_url(simplify)

        image_path = 'campaigns/{}/thumbnail.png'.format(self.uuid)

        request = requests.get(url, stream=True)
        if request.status_code == 200:
            request.raw.decode_content = True
            from io import BytesIO
            S3Data().create(image_path, BytesIO(request.content))
        else:
            if simplify:
                return
            self.generate_static_map(simplify=True)

        self.thumbnail = S3Data().thumbnail_url(self.uuid)

    def update_participants_count(self, participants_count, campaign_type):
        """ Update paricipants count.

        :param participants_count: Participant count number
        :type participants_count: int

        :param campaign_type: Campaign type
        :type campaign_type: str
        """
        if campaign_type in self.participants_count_per_type:
            self.total_participants_count -= self.participants_count_per_type[
                campaign_type
            ]
        self.participants_count_per_type[campaign_type] = participants_count
        self.total_participants_count += participants_count
        self.save()

    def update_data(self, data, uploader):
        """ Update data with new dict.

        :param data: data that will be inserted
        :type data: dict

        :param uploader: uploader who created
        :type uploader: str
        """
        for key, value in data.items():
            setattr(self, key, value)
        self.geometry = parse_json_string(self.geometry)
        self.types = Campaign.parse_types_string(self.types.replace('\'', '"'))
        self.selected_functions = parse_json_string(self.selected_functions)
        self.save(uploader)

    def get_selected_functions_in_string(self):
        """ Get selected function in string
        :return: Get selected function in string
        :rtype: str
        """
        for key, value in self.selected_functions.items():
            try:
                SelectedFunction = getattr(
                    insights_functions, value['function'])
                additional_data = {}
                if 'type' in value:
                    additional_data['type'] = value['type']
                selected_function = SelectedFunction(
                    self,
                    feature=value['feature'],
                    required_attributes=value['attributes'],
                    additional_data=additional_data)

                value['type_required'] = \
                    ('%s' % selected_function.type_required).lower()
                value['manager_only'] = selected_function.manager_only
                value['name'] = selected_function.name()
            except AttributeError:
                value = None
        return json.dumps(self.selected_functions).replace('None', 'null')

    def parse_json_file(self):
        """ Parse json file for this campaign.

        If file is corrupted,
        it will raise Campaign.CorruptedFile exception.
        """
        # campaign data
        if self.json_path:
            try:
                content = S3Data().fetch(self.json_path)
                content_json = parse_json_string(content)
                Campaign.validate(content_json, self.uuid)
                self._content_json = content_json
                attributes = self.get_attributes()
                for key, value in content_json.items():
                    if key in attributes:
                        setattr(self, key, value)
            except json.decoder.JSONDecodeError:
                raise JsonModel.CorruptedFile
        self.types = Campaign.parse_types_string(json.dumps(self.types))

        # geometry data
        if self.geojson_path:
            try:
                content = S3Data().fetch(self.geojson_path)
                geometry = parse_json_string(content)
                self.geometry = geometry
                self._content_json['geometry'] = geometry
            except json.decoder.JSONDecodeError:
                raise JsonModel.CorruptedFile

    def json(self):
        """Returns campaign as json format."""
        return self._content_json

    def render_insights_function(
            self,
            insight_function_id,
            additional_data={},
            insight_function_name=None):
        """Get rendered UI from insight_function

        :param insight_function_id: name of insight function
        :type insight_function_id: str

        :param additional_data: additional data that needed
        :type additional_data:dict

        :param insight_function_name: If there's only insight function name
        :type insight_function_name: str

        :return: rendered UI from insight function
        :rtype: str
        """
        campaign_ui = ''
        try:
            if insight_function_name:
                SelectedFunction = getattr(
                    insights_functions, insight_function_name)
                additional_data['function_name'] = insight_function_name
                additional_data['function_id'] = insight_function_id
                selected_function = SelectedFunction(
                    self,
                    feature=None,
                    required_attributes=None,
                    additional_data=additional_data
                )
            else:
                insight_function = self.selected_functions[insight_function_id]
                SelectedFunction = getattr(
                    insights_functions, insight_function['function'])
                additional_data['function_id'] = insight_function_id
                if 'type' in insight_function:
                    additional_data['type'] = insight_function['type']
                selected_function = SelectedFunction(
                    self,
                    feature=insight_function['feature'],
                    required_attributes=insight_function['attributes'],
                    additional_data=additional_data
                )
        except (AttributeError, KeyError) as e:
            return campaign_ui

        # render UI
        context = {
            'selected_function_name': selected_function.name().split('-')[0],
            'icon': selected_function.icon,
            'widget': selected_function.get_ui_html()
        }
        campaign_ui += render_template(
            'campaign_widget/insight_template.html',
            **context
        )
        return campaign_ui

    def insights_function_data_metadata(self, insight_function_id):
        """Get rendered UI from insight_function

        :param insight_function_id: name of insight function
        :type insight_function_id: str

        :return: rendered UI from insight function
        :rtype: str
        """
        try:
            function = self.selected_functions[insight_function_id]
            SelectedFunction = getattr(
                insights_functions, function['function'])
            selected_function = SelectedFunction(
                self,
                feature=function['feature'],
                required_attributes=function['attributes'])
            return selected_function.metadata()
        except AttributeError as e:
            return {}

    def get_union_polygons(self):
        """Return union polygons"""
        simplify = False
        if len(self.geometry['features']) > 1:
            polygons = []
            for feature in self.geometry['features']:
                polygons.append(shapely_geometry.Polygon(
                    feature['geometry']['coordinates'][0]))
            cascaded_polygons = cascaded_union(polygons)
            simplify = True
        else:
            cascaded_polygons = shapely_geometry.Polygon(
                self.geometry['features'][0]
                ['geometry']['coordinates'][0])

        joined_polygons = cascaded_polygons.buffer(
            0.001, 1, join_style=JOIN_STYLE.mitre
        ).buffer(
            -0.001, 1, join_style=JOIN_STYLE.mitre
        )

        if simplify:
            joined_polygons = simplify_polygon(joined_polygons, 0.001)

        return joined_polygons

    def corrected_coordinates(self, coordinate_to_correct=None):
        """ Corrected geometry of campaign.

        :param coordinate_to_correct: correct this coordinate instead
        :type coordinate_to_correct: list

        :return: corrected coordinated
        :rtype: [str]
        """
        cascaded_polygons = self.get_union_polygons()

        coordinates = []
        if cascaded_polygons:
            if cascaded_polygons.type == 'Polygon':
                cascaded_geojson = mapping(cascaded_polygons)
                coordinates_str = json.dumps(cascaded_geojson['coordinates'])
                coordinates = json.loads(coordinates_str)
            elif cascaded_polygons.type == 'MultiPolygon':
                coordinates = numpy.asarray(
                        cascaded_polygons.envelope.exterior.coords)
                coordinates = coordinates.tolist()

        correct_coordinates = self.swap_coordinates(coordinates)
        return correct_coordinates

    def swap_coordinates(self, coordinates):
        """ Swap coordinate lat and lon for overpass

        :param coordinates: this could be list of coordinates or
            single coordinate
        :type coordinates: list
        """
        correct_coordinate = []
        for coordinate in coordinates:
            if isinstance(coordinate[0], float):
                correct_coordinate.append(
                    [coordinate[1], coordinate[0]]
                )
            else:
                correct_coordinate.extend(self.swap_coordinates(coordinate))
        return correct_coordinate

    def get_bbox(self):
        """ Corrected geometry of campaign.
        :return: corrected coordinated
        :rtype: [str]
        """
        if not self.geometry:
            return []

        geometry = copy.deepcopy(self.geometry)
        geometry['features'][0]['geometry']['coordinates'][0] = \
            self.corrected_coordinates()
        geojson = pygeoj.load(data=geometry)
        return geojson.bbox

    def get_current_status(self):
        """ Get campaign status based on start/end date.

        - active : start date <= now < end date
        - inactive : start date > now or now >= end date
        - remote mapping : inactive and self.remote_projects

        :return: status of campaign
        :rtype: str
        """
        start_datetime = datetime.strptime(
            self.start_date,
            "%Y-%m-%d")
        end_datetime = datetime.strptime(
            self.end_date,
            "%Y-%m-%d")

        status = 'inactive'
        if start_datetime.date() <= date.today():
            if end_datetime.date() > date.today():
                status = 'active'

        if status == 'inactive':
            if self.remote_projects:
                status = 'remote-mapping'
        return status

    def get_type_geojsons(self, type):
        s3 = S3Data()
        # For each type we get first level data.
        response = s3.s3.list_objects(Bucket=s3.bucket,
            Prefix=type,
            Delimiter='/')
        if 'Contents' not in list(response.keys()):
            return None

        contents = response['Contents']
        paths = [c['Key'] for c in contents if 'geojson' in c['Key']]

        # Now we have to download from s3 the geojson and return dictionary.
        geojsons = []

        for path in paths:
            body = s3.s3.get_object(Bucket=s3.bucket, Key=path)['Body']
            data = zlib.decompress(body.read(), 16 + zlib.MAX_WBITS)
            json_data = json.loads(data)

            geojsons.append(json_data)

        return geojsons

    def get_s3_types(self):
        s3 = S3Data()
        objs = s3.s3.list_objects(Bucket=s3.bucket,
            Prefix='campaigns/{}/render/'.format(self.uuid),
            Delimiter='/')

        if 'CommonPrefixes' not in objs:
            return None

        types = [t['Prefix'] for t in objs['CommonPrefixes']]

        return types

    # ----------------------------------------------------------
    # coverage functions
    # ----------------------------------------------------------
    def get_coverage_folder(self):
        """ Return coverage folder for this campaign
        :return: path for coverage folder
        :rtype: str
        """
        from reporter import config
        return os.path.join(
            config.CACHE_DIR,
            'coverage',
            self.uuid
        )

    @staticmethod
    def get_json_folder():
        return os.path.join(
            Config.campaigner_data_folder, 'campaign')

    @staticmethod
    def get_thumbnail_folder():
        return 'campaign/thumbnail'

    @staticmethod
    def serialize(data):
        """Serialize campaign dictionary

        :key data: dictionary
        :type data: dict
        """
        try:
            data['start_date'] = data['start_date'].strftime('%Y-%m-%d')
        except AttributeError:
            pass
        try:
            if data['end_date']:
                data['end_date'] = data['end_date'].strftime('%Y-%m-%d')
        except AttributeError:
            pass
        try:
            if 'edited_at' in data:
                if type(data['edited_at']) is datetime:
                    data['edited_at'] = data['edited_at'].strftime('%Y-%m-%d')
        except AttributeError:
            pass

        json_str = json.dumps(data)
        return json_str

    @staticmethod
    def parse_campaign_data(data, uploader):
        """Validate found dict based on campaign class.
        uuid should be same as uuid file.

        :param data: data that will be inserted
        :type data: dict

        :param uploader: uploader who created
        :type uploader: str
        """
        data['version'] = 1
        if 'version' in data:
            data['version'] = data['version'] + 1
        data['edited_by'] = uploader
        data['campaign_creator'] = uploader

        uuid = data['uuid']
        data['types'] = Campaign.parse_types_string(data['types'])
        data['selected_functions'] = parse_json_string(
            data['selected_functions'])
        Campaign.validate(data, uuid)
        return data

    @staticmethod
    def parse_types_string(types_string):
        types = parse_json_string(types_string)
        for type, value in types.items():
            json_tags = {}
            tags = value['tags']
            if (isinstance(tags, list)):
                for tag in value['tags']:
                    tag = tag.replace(']', '')
                    tag_splitted = tag.split('[')
                    tag_key = tag_splitted[0].strip()
                    if len(tag_splitted) == 2:
                        json_tags[tag_key] = tag_splitted[1].split(',')
                    else:
                        json_tags[tag_key] = []
                value['tags'] = json_tags
        return types

    def calculate_areas_covered(self):
        completed_areas = 0
        for area in self.geometry['features']:
            if 'status' in area['properties']:
                if area['properties']['status'] == 'complete':
                    completed_areas += 1

        total_areas = len(self.geometry['features'])
        return int((completed_areas / total_areas) * 100)

    @staticmethod
    def create(data, uploader):
        """Validate found dict based on campaign class.
        uuid should be same as uuid file.

        :param data: data that will be inserted
        :type data: dict

        :param uploader: uploader who created
        :type uploader: str
        """
        campaign_data = Campaign.parse_campaign_data(data, uploader)
        geometry = data['geometry']
        del data['geometry']

        json_str = Campaign.serialize(
            Campaign.parse_campaign_data(data, uploader)
        )

        campaign_key = Campaign.get_json_file(campaign_data['uuid'])
        campaign_body = json_str
        S3Data().create(campaign_key, campaign_body)

        geocampaign_key = Campaign.get_geojson_file(campaign_data['uuid'])
        geocampaign_body = json.dumps(parse_json_string(geometry))
        S3Data().create(geocampaign_key, geocampaign_body)

    @staticmethod
    def all(campaign_status=None, **kwargs):
        """Get all campaigns

        :param campaign_status: status of campaign, active or inactive
        :type campaign_status: str

        :return: Campaigns that found or none
        :rtype: [Campaign]
        """
        sort_list = []
        campaigns = []
        for campaign_uuid in S3Data().list('campaigns'):
            try:
                campaign = Campaign.get(campaign_uuid)
                if campaign_status == 'all':
                    allowed = True
                elif campaign_status == campaign.get_current_status():
                    allowed = True
                else:
                    allowed = False
                if allowed:
                    sort_object = campaign.name

                    if 'sort_by' in kwargs:
                        if kwargs['sort_by'][0] == 'recent':
                            sort_object = int(
                                datetime.today().strftime('%s')
                            ) - int(
                                datetime.strptime(
                                    campaign.edited_at,
                                    "%a %b %d %H:%M:%S %Y"
                                ).strftime('%s'))

                    position = bisect.bisect(sort_list, sort_object)
                    bisect.insort(sort_list, sort_object)
                    campaigns.insert(position, campaign)
            except Campaign.DoesNotExist:
                pass

        if 'per_page' in kwargs:
            per_page = int(kwargs['per_page'][0])

            page = 1
            if 'page' in kwargs:
                page = int(kwargs['page'][0])

            start_index = (page - 1) * per_page

            campaigns = campaigns[start_index:start_index + per_page]

        return campaigns

    @staticmethod
    def nearest_campaigns(coordinate, campaign_status, **kwargs):
        """Return nearest campaigns based on coordinate

        :param campaign_status: status of campaign, active or inactive
        :type campaign_status: str

        :param coordinate: lat, long coordinate string
        :type coordinate: str
        """
        campaigns = []
        sort_list = []
        coordinates = coordinate.split(',')
        point = shapely_geometry.Point(
            [float(coordinates[1]), float(coordinates[0])])
        per_page = None
        is_close = False
        circle_buffer = None

        if 'per_page' in kwargs:
            is_close = True
            per_page = int(kwargs['per_page'][0])
        else:
            circle_buffer = point.buffer(4)

        for campaign in S3Data().list('campaign'):
            try:
                campaign_uuid, extension = campaign.split('.')
                if extension != 'json':
                    continue
                campaign = Campaign.get(campaign_uuid)

                polygon = campaign.get_union_polygons()

                if circle_buffer:
                    if circle_buffer.contains(polygon):
                        is_close = True

                if is_close:

                    if campaign_status == 'all':
                        allowed = True
                    elif campaign_status == campaign.get_current_status():
                        allowed = True
                    else:
                        allowed = False

                    if allowed:
                        if per_page:
                            distance = point.distance(polygon.centroid)
                            position = bisect.bisect(sort_list,
                                                     distance)
                            bisect.insort(sort_list, distance)
                            campaigns.insert(position, campaign)
                        else:
                            campaigns.append(campaign)

                    if not per_page:
                        is_close = False

            except Campaign.DoesNotExist:
                pass

        if per_page:

            page = 1
            if 'page' in kwargs:
                page = int(kwargs['page'][0])

            start_index = (page - 1) * per_page

            campaigns = campaigns[start_index:start_index + per_page]

        return campaigns

    @staticmethod
    def get(uuid):
        """Get campaign from uuid

        :param uuid: UUID of campaign that to be returned
        :type uuid: str

        :return: Campaign that found or none
        :rtype: Campaign
        """
        return Campaign(uuid)

    @staticmethod
    def get_json_file(uuid):
        """ Get path of json file of uuid.
        :param uuid: UUID of json model that to be returned
        :type uuid: str

        :return: path of json or none if not found
        :rtype: str
        """
        return 'campaigns/{}/campaign.json'.format(uuid)

    @staticmethod
    def get_geojson_file(uuid):
        """ Get path of geojson file of uuid.
        :param uuid: UUID of json model that to be returned
        :type uuid: str

        :return: path of json or none if not found
        :rtype: str
        """
        return 'campaigns/{}/campaign.geojson'.format(uuid)

    @staticmethod
    def validate(data, uuid):
        """Validate found dict based on campaign class.
        uuid should be same as uuid file.

        :param data: data that will be inserted
        :type data: dict

        :param uuid: UUID of campaign
        :type uuid: str
        """
        required_attributes = [
            'uuid', 'version', 'campaign_creator', 'edited_by', 'name']
        for required_attribute in required_attributes:
            if required_attribute not in data:
                raise JsonModel.RequiredAttributeMissed(required_attribute)
            if uuid != data['uuid']:
                raise Exception('UUID is not same in json.')
        return True

    @staticmethod
    def compute(campaign_uuid):
        """
        Invoke the compute lambda function.
        """
        import boto3
        from app import osm_app
        aws_lambda = boto3.client('lambda')

        function_name = "{env}_compute_campaign".format(
            env=osm_app.config['ENV'])

        payload = json.dumps({"campaign_uuid": campaign_uuid})

        aws_lambda.invoke(
            FunctionName=function_name,
            InvocationType="Event",
            Payload=payload)

    @staticmethod
    class DoesNotExist(Exception):
        def __init__(self):
            self.message = "Campaign doesn't exist"
            super(Campaign.DoesNotExist, self).__init__(self.message)

    @staticmethod
    class GeometryDoesNotExist(Exception):
        def __init__(self):
            self.message = "Campaign Geometry doesn't exist"
            super(Campaign.GeometryDoesNotExist, self).__init__(self.message)

    @staticmethod
    class InsightsFunctionNotAssignedToCampaign(Exception):
        def __init__(self):
            self.message = "" \
                           "This insights function not " \
                           "assigned to this campaign"
            super(
                Campaign.InsightsFunctionNotAssignedToCampaign, self). \
                __init__(self.message)
