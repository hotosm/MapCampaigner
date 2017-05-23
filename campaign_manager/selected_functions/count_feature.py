__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

from campaign_manager.selected_functions._abstract_insights_function import (
    AbstractInsightsFunction
)


class CountFeature(AbstractInsightsFunction):
    function_name = "Count feature"
    category = ['quality']
    need_required_attributes = False

    def get_ui_html_file(self):
        """ Get ui name in templates
        :return: string name of html
        :rtype: str
        """
        return "piechart"

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

    def post_process_data(self, data):
        """ Process data regarding output.
        This needed for processing data for counting or grouping.

        :param data: Data that received from open street map
        :type data: dict

        :return: Processed data
        :rtype: dict
        """
        output = {}
        for current_data in data:
            building_key = 'building'
            if building_key not in current_data:
                building_key = 'amenity'

            try:
                building_type = current_data[building_key]
            except KeyError:
                building_type = 'unknown'

            if building_type not in output:
                output[building_type] = 0
            output[building_type] += 1

        return output
