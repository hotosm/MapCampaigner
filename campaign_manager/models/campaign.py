__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '10/05/17'

import time
import json
import os
import campaign_manager.selected_functions as selected_functions

from flask import render_template

from campaign_manager.models.json_model import JsonModel
from campaign_manager.utilities import module_path


class Campaign(JsonModel):
    """
    Class campaign model that hold campaign information and functions.
    """
    uuid = ''
    name = ''
    campaign_creator = ''
    campaign_status = ''
    coverage = ''
    geometry = None
    start_date = None
    end_date = None
    campaign_managers = []
    selected_functions = []

    def __init__(self, uuid):
        self.uuid = uuid
        self.json_path = Campaign.get_json_file(uuid)
        self.edited_at = time.ctime(os.path.getmtime(self.json_path))
        self.parse_json_file()

    def update_data(self, dict, uploader):
        """ Update data with new dict.
        """
        for key, value in dict.items():
            setattr(self, key, value)
        self.version += 1
        self.edited_by = uploader

        # save updated campaign to json
        dict = self.to_dict()
        Campaign.validate(dict, self.uuid)
        json_str = Campaign.serialize(dict)
        json_path = os.path.join(
            Campaign.get_json_folder(), '%s.json' % self.uuid
        )
        _file = open(json_path, 'w+')
        _file.write(json_str)
        _file.close()

    def parse_json_file(self):
        """ Parse json file for this campaign.

        If file is corrupted,
        it will raise Campaign.CorruptedFile exception.
        """
        if self.json_path:
            try:
                _file = open(self.json_path, 'r')
                content = _file.read()
                content_json = json.loads(content)
                Campaign.validate(content_json, self.uuid)
                attributes = self.get_attributes()
                for key, value in content_json.items():
                    if key in attributes:
                        setattr(self, key, value)
            except json.decoder.JSONDecodeError:
                raise JsonModel.CorruptedFile

    def render_side_bar(self):
        """Testing for render sidebar"""
        campaing_ui = ''
        for selected_function_name in self.selected_functions:
            try:
                SelectedFunction = getattr(
                    selected_functions, selected_function_name)
                selected_function = SelectedFunction(self)

                if selected_function.function_name:
                    function_name = selected_function.function_name
                else:
                    function_name = selected_function_name

                context = {
                    'selected_function_name': function_name,
                    'widget': selected_function.get_ui_html()
                }
                campaing_ui += render_template(
                    'campaign_widget/sidebar.html',
                    **context
                )
            except AttributeError:
                pass

        return campaing_ui

    @staticmethod
    def get_json_folder():
        return os.path.join(
            module_path(), 'campaigns_data', 'campaign')

    @staticmethod
    def serialize(dict):
        """Serialize campaign dictionary

        :key dict: dictionary
        :type dict: dict
        """
        dict['start_date'] = dict['start_date'].strftime('%Y-%m-%d')
        if dict['end_date']:
            dict['end_date'] = dict['end_date'].strftime('%Y-%m-%d')
        json_str = json.dumps(dict)
        return json_str

    @staticmethod
    def create(dict, uploader):
        """Validate found dict based on campaign class.
        uuid should be same as uuid file.
        """
        dict['version'] = 1
        dict['edited_by'] = uploader
        dict['campaign_creator'] = uploader

        uuid = dict['uuid']
        Campaign.validate(dict, uuid)

        json_str = Campaign.serialize(dict)
        json_path = os.path.join(
            Campaign.get_json_folder(), '%s.json' % uuid
        )
        _file = open(json_path, 'w+')
        _file.write(json_str)
        _file.close()

    @staticmethod
    def all():
        """Get all campaigns

        :return: Campaigns that found or none
        :rtype: [Campaign]
        """
        campaigns = []
        for root, dirs, files in os.walk(Campaign.get_json_folder()):
            for file in files:
                try:
                    campaigns.append(Campaign.get(os.path.splitext(file)[0]))
                except Campaign.DoesNotExist:
                    pass
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
    def validate(dict, uuid):
        """Validate found dict based on campaign class.
        uuid should be same as uuid file.
        """
        required_attributes = [
            'uuid', 'version', 'campaign_creator', 'edited_by', 'name']
        for required_attribute in required_attributes:
            if required_attribute not in dict:
                raise JsonModel.RequiredAttributeMissed(required_attribute)
            if uuid != dict['uuid']:
                raise Exception('UUID is not same in json.')
        return True

    @staticmethod
    class DoesNotExist(Exception):
        def __init__(self):
            self.message = "Campaign doesn't exist"
            super(Campaign.DoesNotExist, self).__init__(self.message)
