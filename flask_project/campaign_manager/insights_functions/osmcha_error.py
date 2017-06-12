__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

from campaign_manager.insights_functions._abstract_insights_function import (
    AbstractInsightsFunction
)

from campaign_manager.data_providers.osmcha_provider import OsmchaProvider


class OsmchaError(AbstractInsightsFunction):
    function_name = "Showing osmcha error"
    category = ['error']
    icon = 'list'

    # attribute of insight function
    need_feature = False
    need_required_attributes = False
    current_page = 1
    function_id = ''

    def initiate(self, additional_data):
        """ Initiate function

        :param additional_data: additional data that needed
        :type additional_data:dict
        """
        if 'page' in additional_data:
            self.current_page = int(additional_data['page'])

    def get_ui_html_file(self):
        """ Get ui name in templates
        :return: string name of html
        :rtype: str
        """
        return "osmcha_error"

    def get_summary_html_file(self):
        """ Get summary name in templates
        :return: string name of html
        :rtype: str
        """
        return ""

    def get_details_html_file(self):
        """ Get summary name in templates
        :return: string name of html
        :rtype: str
        """
        return ""

    def get_data_from_provider(self):
        """ Get data provider function
        :return: data from provider
        :rtype: dict
        """
        bbox = self.campaign.get_bbox()
        input_bbox = []
        if bbox:
            input_bbox.append(bbox[2])
            input_bbox.append(bbox[0])
            input_bbox.append(bbox[3])
            input_bbox.append(bbox[1])

        return OsmchaProvider().get_data(
            input_bbox, self.current_page)

    def process_data(self, raw_datas):
        """ Process data from raw.
        :param raw_datas: Raw data that returns by function provider
        :type raw_datas: dict

        :return: processed data
        :rtype: dict
        """
        raw_datas['uuid'] = self.campaign.uuid
        return raw_datas
