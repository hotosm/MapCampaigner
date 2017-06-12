__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

from datetime import datetime
from campaign_manager.insights_functions._abstract_insights_function import (
    AbstractInsightsFunction
)

from campaign_manager.data_providers.osmcha_changeset_provider import OsmchaChangesetProvider


class OsmchaChangesets(AbstractInsightsFunction):
    function_name = "Showing osmcha changesets"
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

        start_date = self.campaign.start_date
        end_date = self.campaign.end_date
        return OsmchaChangesetProvider().get_data(
            input_bbox, self.current_page,
            start_date=start_date, end_date=end_date)

    def process_data(self, raw_datas):
        """ Process data from raw.
        :param raw_datas: Raw data that returns by function provider
        :type raw_datas: dict

        :return: processed data
        :rtype: dict
        """
        raw_datas['uuid'] = self.campaign.uuid
        raw_datas['headers'] = [
            'uid', 'date', 'user', 'comment', 'count', 'reasons',
            'checked', 'check_date'
        ]

        data = raw_datas['data']['features']
        clean_data = []
        for row in data:
            properties = row['properties']
            check_date = None
            if properties['check_date']:
                check_date = datetime.strptime(
                    properties['check_date'], '%Y-%m-%dT%H:%M:%SZ').strftime(
                    "%Y-%m-%d %H:%M"),
            clean_data.append({
                'ID': properties['uid'],
                'Date': datetime.strptime(
                    properties['date'], '%Y-%m-%dT%H:%M:%SZ').strftime(
                    "%Y-%m-%d %H:%M"),
                'User': properties['user'],
                'Comment': properties['comment'],
                'Count': {
                    'create': properties['create'],
                    'modify': properties['modify'],
                    'delete': properties['delete'],
                },
                'Reasons': ', '.join(
                    [comment['name'] for comment in properties['reasons']]),
                "Suspected": properties['is_suspect'],
                "Harmful": properties['harmful'],
                "Checked": properties['checked'],
                "Check date": check_date,
            })
        raw_datas['data'] = clean_data
        return raw_datas
