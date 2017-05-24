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
    description = ''

    def __init__(self, uuid):
        self.uuid = uuid
        self.json_path = Campaign.get_json_file(uuid)
        self.edited_at = time.ctime(os.path.getmtime(self.json_path))
        self.parse_json_file()

    def update_data(self, data, uploader):
        """ Update data with new dict.

        :param data: data that will be inserted
        :type data: dict

        :param uploader: uploader who created
        :type uploader: str
        """
        for key, value in data.items():
            setattr(self, key, value)
        self.geometry = json.loads(self.geometry)
        self.selected_functions = json.loads(self.selected_functions)
        self.version += 1
        self.edited_by = uploader

        # save updated campaign to json
        data = self.to_dict()
        Campaign.validate(data, self.uuid)
        json_str = Campaign.serialize(data)
        json_path = os.path.join(
            Campaign.get_json_folder(), '%s.json' % self.uuid
        )
        _file = open(json_path, 'w+')
        _file.write(json_str)
        _file.close()

    def get_selected_functions_in_string(self):
        """ Get selected function in string
        :return: Get selected function in string
        :rtype: str
        """
        return json.dumps(self.selected_functions).replace('None', 'null');

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

    def insight_function_data(self, insight_function_id):
        """Get data from insight_function

        :param insight_function_id: id of insight function
        :type insight_function_id: str

        :return: data from insight function
        :rtype: dict
        """
        if insight_function_id not in self.selected_functions:
            raise Campaign.InsightsFunctionNotAssignedToCampaign
        try:
            function = self.selected_functions[insight_function_id]
            SelectedFunction = getattr(
                selected_functions, function['function'])
            selected_function = SelectedFunction(
                self,
                feature=function['feature'],
                required_attributes=function['attributes'])
            selected_function.run()
            output = {
                'title': selected_function.name(),
                'data': selected_function.get_function_data()
            }
            return output
        except AttributeError as e:
            return {}

    def render_insights_function(self, insight_function_id):
        """Get rendered UI from insight_function

        :param insight_function_id: name of insight function
        :type insight_function_id: str

        :return: rendered UI from insight function
        :rtype: str
        """
        campaing_ui = ''
        try:
            function = self.selected_functions[insight_function_id]
            SelectedFunction = getattr(
                selected_functions, function['function'])
            selected_function = SelectedFunction(
                self,
                feature=function['feature'],
                required_attributes=function['attributes'])
        except AttributeError as e:
            return campaing_ui

        # render UI
        context = {
            'selected_function_name': selected_function.name().split('-')[0],
            'icon': selected_function.icon,
            'widget': selected_function.get_ui_html()
        }
        campaing_ui += render_template(
            'campaign_widget/insight_template.html',
            **context
        )
        return campaing_ui

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
                selected_functions, function['function'])
            selected_function = SelectedFunction(
                self,
                feature=function['feature'],
                required_attributes=function['attributes'])
            return selected_function.metadata()
        except AttributeError as e:
            return {}

    @staticmethod
    def get_json_folder():
        return os.path.join(
            module_path(), 'campaigns_data', 'campaign')

    @staticmethod
    def serialize(data):
        """Serialize campaign dictionary

        :key data: dictionary
        :type data: dict
        """
        data['start_date'] = data['start_date'].strftime('%Y-%m-%d')
        if data['end_date']:
            data['end_date'] = data['end_date'].strftime('%Y-%m-%d')
        json_str = json.dumps(data)
        return json_str

    @staticmethod
    def create(data, uploader):
        """Validate found dict based on campaign class.
        uuid should be same as uuid file.

        :param data: data that will be inserted
        :type data: dict

        :param uploader: uploader who created
        :type uploader: str
        """
        data['version'] = 1
        data['edited_by'] = uploader
        data['campaign_creator'] = uploader

        uuid = data['uuid']
        Campaign.validate(data, uuid)
        data['geometry'] = json.loads(data['geometry'])
        data['selected_functions'] = json.loads(data['selected_functions'])

        json_str = Campaign.serialize(data)
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
    class InsightsFunctionNotAssignedToCampaign(Exception):
        def __init__(self):
            self.message = "" \
                           "This insights function not " \
                           "assigned to this campaign"
            super(
                Campaign.InsightsFunctionNotAssignedToCampaign, self).__init__(
                self.message)
