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

    def __init__(self, uuid=None):
        if uuid:
            self.uuid = uuid
            self.json_path = Campaign.get_json_file(uuid)
            self.edited_at = time.ctime(os.path.getmtime(self.json_path))
            self.geojson_path = Campaign.get_geojson_file(uuid)
            self.parse_json_file()

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
        json_str = Campaign.serialize(data)
        json_path = os.path.join(
            Campaign.get_json_folder(), '%s.json' % self.uuid
        )
        _file = open(json_path, 'w+')
        _file.write(json_str)
        _file.close()

        # save geometry campaign to geojson
        geometry_str = json.dumps(geometry)
        geometry_path = os.path.join(
            Campaign.get_json_folder(), '%s.geojson' % self.uuid
        )
        _file = open(geometry_path, 'w+')
        _file.write(geometry_str)
        _file.close()

        # create commit as git
        if save_to_git:
            try:
                save_with_git(
                    'Update campaign - %s' % self.uuid
                )
            except Exception as e:
                print(e)

    def generate_static_map(self):
        """
        Download static map from http://staticmap.openstreetmap.de with marker,
        then save it thumbnail folder
        """
        try:
            from secret import MAPBOX_TOKEN
            url = 'https://api.mapbox.com/styles/v1/hot/' \
                  'cj7hdldfv4d2e2qp37cm09tl8/static/geojson({overlay})/' \
                  'auto/{width}x{height}?' \
                  'access_token=' + MAPBOX_TOKEN
            if len(self.geometry['features']) > 1:
                geometry = {
                    'type': 'Feature',
                    'properties': {},
                    'geometry': mapping(self.get_union_polygons())
                }
                geometry = json.dumps(geometry, separators=(',', ':'))
            else:
                geometry = json.dumps(
                    self.geometry['features'][0],
                    separators=(',', ':'))
            url = url.format(
                overlay=geometry,
                width=512,
                height=300
            )

        except ImportError:
            url = 'http://staticmap.openstreetmap.de/staticmap.php?' \
                  'center=0.0,0.0&zoom=1&size=512x512&maptype=mapnik'
            polygon = self.get_union_polygons()
            marker_url = '&markers=%s,%s,lightblue' % (
                polygon.centroid.y, polygon.centroid.x)
            url = url + marker_url

        safe_name = hashlib.md5(url.encode('utf-8')).hexdigest() + '.png'
        thumbnail_dir = os.path.join(Campaign.get_json_folder(), 'thumbnail')

        if not os.path.exists(thumbnail_dir):
            os.makedirs(thumbnail_dir)

        image_path = os.path.join(
            thumbnail_dir, safe_name
        )

        if not os.path.exists(image_path):
            request = requests.get(url, stream=True)
            if request.status_code == 200:
                with open(image_path, 'wb') as f:
                    request.raw.decode_content = True
                    shutil.copyfileobj(request.raw, f)

        self.thumbnail = safe_name

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
                _file = open(self.json_path, 'r')
                content = _file.read()
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
                _file = open(self.geojson_path, 'r')
                content = _file.read()
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

    def get_json_type(self, type):
        """ Get survey of campaign types in json.
        :return: json surveys of types
        :rtype: dict
        """
        if not type:
            return {}
        # getting features and required attributes from types
        survey_folder = os.path.join(
            Config.campaigner_data_folder,
            'surveys'
        )
        survey_file = os.path.join(
            survey_folder,
            type
        )
        return get_survey_json(survey_file)

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

    # ----------------------------------------------------------
    # coverage functions
    # ----------------------------------------------------------
    def get_coverage_folder(self):
        """ Return coverage folder for this campaign
        :return: path for coverage folder
        :rtype: str
        """
        return os.path.join(
            Config.campaigner_data_folder,
            'coverage',
            self.uuid
        )

    @staticmethod
    def get_json_folder():
        return os.path.join(
            Config.campaigner_data_folder, 'campaign')

    @staticmethod
    def get_thumbnail_folder():
        return os.path.join(
            Campaign.get_json_folder(), 'thumbnail')

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

        # save updated campaign to json
        json_path = os.path.join(
            Campaign.get_json_folder(), '%s.json' % campaign_data['uuid']
        )
        _file = open(json_path, 'w+')
        _file.write(json_str)
        _file.close()

        # save geometry campaign to geojson
        geojson_path = os.path.join(
            Campaign.get_json_folder(),
            '%s.geojson' % campaign_data['uuid']
        )
        _file = open(geojson_path, 'w+')
        _file.write(json.dumps(parse_json_string(geometry)))
        _file.close()

        # create commit as git
        try:
            save_with_git(
                'Create campaign - %s' % data['uuid']
            )
        except Exception as e:
            print(e)

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
        for root, dirs, files in os.walk(Campaign.get_json_folder()):
            for file in files:
                try:
                    campaign_uuid, extension = os.path.splitext(file)
                    if extension != '.json':
                        continue
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

        for root, dirs, files in os.walk(Campaign.get_json_folder()):
            for file in files:
                try:
                    campaign_uuid, extension = os.path.splitext(file)
                    if extension != '.json':
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
        json_path = os.path.join(
            Campaign.get_json_folder(), '%s.json' % uuid
        )
        if os.path.isfile(json_path):
            return json_path
        else:
            raise Campaign.DoesNotExist()

    @staticmethod
    def get_geojson_file(uuid):
        """ Get path of geojson file of uuid.
        :param uuid: UUID of json model that to be returned
        :type uuid: str

        :return: path of json or none if not found
        :rtype: str
        """
        json_path = os.path.join(
            Campaign.get_json_folder(), '%s.geojson' % uuid
        )
        if os.path.isfile(json_path):
            return json_path
        else:
            return None

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
