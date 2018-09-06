import json
import os
from dependencies.shapely import geometry
from json_model import JsonModel
from utilities import (
    parse_json_string,
    simplify_polygon
)
from aws import S3Data


class Campaign(JsonModel):
    """
    Class campaign model that hold campaign information and functions.
    """
    uuid = ''
    geometry = None
    types = []
    _content_json = None
    start_date = None
    end_date = None

    def __init__(self, uuid=None):
        if uuid:
            self.uuid = uuid
            self.json_path = Campaign.get_json_file(uuid)
            self.geojson_path = Campaign.get_geojson_file(uuid)
            self.edited_at = S3Data().get_last_modified_date(self.json_path)
            self.parse_json_file()

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

    def get_union_polygons(self):
        """Return union polygons"""
        simplify = False
        if len(self.geometry['features']) > 1:
            polygons = []
            for feature in self.geometry['features']:
                polygons.append(geometry.Polygon(
                    feature['geometry']['coordinates'][0]))
            cascaded_polygons = cascaded_union(polygons)
            simplify = True
        else:
            cascaded_polygons = geometry.Polygon(
                self.geometry['features'][0]
                ['geometry']['coordinates'][0])

        joined_polygons = cascaded_polygons.buffer(
            0.001, 1, join_style=geometry.JOIN_STYLE.mitre
        ).buffer(
            -0.001, 1, join_style=geometry.JOIN_STYLE.mitre
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
                cascaded_geojson = geometry.mapping(cascaded_polygons)
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
