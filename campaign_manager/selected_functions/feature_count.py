__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

from campaign_manager.selected_functions._abstract_insights_function import (
    AbstractInsightsFunction
)


class FeatureCount(AbstractInsightsFunction):
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
        return ""

    def process_data(self, raw_data):
        """ Get geometry of campaign.
        :param raw_data: Raw data that returns by function provider
        :type raw_data: dict

        :return: processed data
        :rtype: dict
        """
        return raw_data
