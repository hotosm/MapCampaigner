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

    def post_process_data(self, data):
        """ Process data regarding output.
        This needed for processing data for counting or grouping.

        :param data: Data that received from open street map
        :type data: dict

        :return: Processed data
        :rtype: dict
        """
        dict = {}
        feature_extracted = self.FEATURES_MAPPING[self.feature]
        for current_data in data:
            building_type = current_data[feature_extracted]
            if building_type not in dict:
                dict[building_type] = 0
            dict[building_type] += 1
        return dict
