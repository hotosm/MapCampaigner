__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

from app_config import Config
from datetime import datetime
from campaign_manager.insights_functions._abstract_insights_function import (
    AbstractInsightsFunction
)
from campaign_manager.data_providers.osmcha_changesets_provider import (
    OsmchaChangesetsProvider
)


class OsmchaChangesets(AbstractInsightsFunction):
    function_name = "Osmcha changesets"
    icon = 'list'

    current_page = 1
    max_page = 100
    function_id = ''

    def initiate(self, additional_data):
        """ Initiate function

        :param additional_data: additional data that needed
        :type additional_data:dict
        """
        if 'page' in additional_data:
            self.current_page = int(additional_data['page'])
        if 'type' in additional_data:
            self.feature_type = additional_data['type']
        if 'max_page' in additional_data:
            self.max_page = additional_data['max_page']

    def get_ui_html_file(self):
        """ Get ui name in templates
        :return: string name of html
        :rtype: str
        """
        return "osmcha_changesets"

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
        return OsmchaChangesetsProvider().get_data(
                geometry,
                self.current_page,
                start_date=start_date,
                end_date=end_date,
                max_page=self.max_page)

    def process_data(self, raw_data):
        """ Process data from raw.
        :param raw_data: Raw data that returns by function provider
        :type raw_data: dict

        :return: processed data
        :rtype: dict
        """

        raw_data['osmcha_url'] = Config().OSMCHA_FRONTEND_URL
        raw_data['uuid'] = self.campaign.uuid
        raw_data['headers'] = [
            'uid', 'date', 'user', 'comment', 'count', 'reasons',
            'checked', 'check_date'
        ]

        if 'data' in raw_data and 'features' in raw_data['data']:
            data = raw_data['data']['features']
            clean_data = []
            for row in data:
                properties = row['properties']
                check_date = None
                if properties['check_date']:
                    check_date = datetime.strptime(
                        properties['check_date'],
                        '%Y-%m-%dT%H:%M:%S.%fZ').strftime(
                        "%Y-%m-%d %H:%M"),
                clean_data.append({
                    'ChangeSetId': row['id'],
                    'ID': properties['uid'],
                    'Date': datetime.strptime(
                        properties['date'],
                        '%Y-%m-%dT%H:%M:%SZ').strftime(
                        "%Y-%m-%d %H:%M"),
                    'User': properties['user'],
                    'Comment': properties['comment'],
                    'Features': properties['features'],
                    'Count': {
                        'create': properties['create'],
                        'modify': properties['modify'],
                        'delete': properties['delete'],
                    },
                    'Reasons': ', '.join(
                        [comment['name'] for comment in properties['reasons']]
                    ),
                    "Suspected": properties['is_suspect'],
                    "Harmful": properties['harmful'],
                    "Checked": properties['checked'],
                    "Check date": check_date,
                })
            raw_data['data'] = clean_data
        return raw_data
