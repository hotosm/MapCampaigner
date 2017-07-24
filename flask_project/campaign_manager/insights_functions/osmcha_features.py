__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '13/06/17'

from app_config import Config
from datetime import datetime
from campaign_manager.insights_functions._abstract_insights_function import (
    AbstractInsightsFunction
)
from campaign_manager.data_providers.osmcha_features_provider import (
    OsmchaFeaturesProvider
)


class OsmchaFeatures(AbstractInsightsFunction):
    function_name = "Osmcha features"
    icon = 'list'

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
        return "osmcha_features"

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
        geometry = self.campaign.geometry
        start_date = self.campaign.start_date
        end_date = self.campaign.end_date
        return OsmchaFeaturesProvider().get_data(
            geometry, self.current_page,
            start_date=start_date, end_date=end_date)

    def process_data(self, raw_data):
        """ Process data from raw.
        :param raw_data: Raw data that returns by function provider
        :type raw_data: dict

        :return: processed data
        :rtype: dict
        """
        raw_data['osmcha_url'] = Config().OSMCHA_FRONTEND_URL
        raw_data['uuid'] = self.campaign.uuid

        if 'data' in raw_data and 'features' in raw_data['data']:
            data = raw_data['data']['features']
            clean_data = []
            for row in data:
                properties = row['properties']
                clean_data.append({
                    'ID': {
                        'osm_id': properties['osm_id'],
                        'osm_link': properties['osm_link'],
                    },
                    'Date': datetime.strptime(
                        properties['date'],
                        '%Y-%m-%dT%H:%M:%SZ').strftime(
                        "%Y-%m-%d %H:%M"),
                    'Changeset': properties['changeset'],
                    'Comment': properties['comment'],
                    'Reasons': ', '.join(
                        [comment['name'] for comment in properties['reasons']]
                    ),
                })
            raw_data['data'] = clean_data
        return raw_data
