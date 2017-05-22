__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

from campaign_manager.selected_functions._abstract_insights_function import (
    AbstractInsightsFunction
)


class GetCountBuildingByType(AbstractInsightsFunction):
    function_name = "Get count based on type building "

    def get_ui_html_file(self):
        """ Get ui name in templates
        :return: string name of html
        :rtype: str
        """
        return ""

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

    def get_required_attributes(self):
        """ Get required attributes for function provider.
        :return: list of required attributes
        :rtype: [str]
        """
        return {
            "name": None,
            "building": None
        }

    def get_feature(self):
        """ Get feature that needed for openstreetmap.

        :param feature: The type of feature to extract:
            buildings, building-points, roads, potential-idp, boundary-[1,11]
        :type feature: str
        """
        return 'building'

    def post_process_data(self, data):
        """ Process data regarding output.
        This needed for processing data for counting or grouping.

        :param data: Data that received from open street map
        :type data: dict

        :return: Processed data
        :rtype: dict
        """
        dict = {}
        for current_data in data:
            building_type = current_data['building']
            if building_type not in dict:
                dict[building_type] = 0
            dict[building_type] += 1
        return dict
