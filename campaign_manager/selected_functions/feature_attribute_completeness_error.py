__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

from campaign_manager.selected_functions._abstract_insights_function import (
    AbstractInsightsFunction
)


class FeatureAttributeCompletenessError(AbstractInsightsFunction):
    function_name = "Showing list error of feature"
    category = ['error']
    need_required_attributes = True
    icon = 'list'

    def get_ui_html_file(self):
        """ Get ui name in templates
        :return: string name of html
        :rtype: str
        """
        return "feature_list"

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
        metadata = self.metadata()
        required_attributes = {}
        required_attributes.update(self.get_required_attributes())
        output = {
            'attributes': required_attributes,
            'data': self._function_good_data
        }
        return output
