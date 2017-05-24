__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

from campaign_manager.selected_functions._abstract_insights_function import (
    AbstractInsightsFunction
)


class FeatureAttributeCompleteness(AbstractInsightsFunction):
    function_name = "Feature attribute completeness"
    category = ['quality']
    need_required_attributes = True
    icon = 'percent'

    def get_ui_html_file(self):
        """ Get ui name in templates
        :return: string name of html
        :rtype: str
        """
        return "progress_bar"

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
        output = {
            'percentage': '%.4f' % (
                (len(data) / metadata['collected_data_count']) * 100
            ),
            'complete': len(data),
            'total': metadata['collected_data_count']
        }
        return output
