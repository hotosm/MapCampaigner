import json
import os
from json_model import JsonModel
from utilities import parse_json_string
from aws import S3Data


class Campaign(JsonModel):
    """
    Class campaign model that hold campaign information and functions.
    """
    uuid = ''
    geometry = None
    types = []
    _content_json = None

    def __init__(self, uuid=None):
        if uuid:
            self.uuid = uuid
            self.json_path = Campaign.get_json_file(uuid)
            self.geojson_path = Campaign.get_geojson_file(uuid)
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
