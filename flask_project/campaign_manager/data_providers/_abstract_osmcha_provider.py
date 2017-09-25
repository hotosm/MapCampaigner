__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '12/06/17'

import json
import requests
from app_config import Config
from urllib.error import HTTPError
from campaign_manager.utilities import multi_feature_to_polygon
from campaign_manager.data_providers._abstract_data_provider import (
    AbstractDataProvider
)


class AbstractOsmchaProvider(AbstractDataProvider):
    """Data from osmcha"""
    limit_per_page = 15

    def get_api_url(self):
        """ Return url of osmcha

        :return: url
        :rtype:str
        """
        raise NotImplementedError()

    def get_data(self,
                 geometry,
                 page=1,
                 start_date='',
                 end_date='',
                 max_page=None):
        """Get data from osmcha.
        :param geometry: geometry that used by osmcha
        :type geometry: dict

        :param page: page that used by osmcha
        :type page: int

        :param start_date: start_date that used by osmcha
        :type start_date: str

        :param end_date: end_date that used by osmcha
        :type end_date: str

        :returns: A data from osmcha
        :rtype: dict
        """
        try:
            if max_page:
                self.limit_per_page = max_page

            single_geometry = multi_feature_to_polygon(geometry)
            payload_geometry = json.dumps(
                    single_geometry['features'][0]['geometry'])
            payload = {
                'page': page,
                'page_size': self.limit_per_page,
                'geometry': payload_geometry,
                'date__gte': start_date,
                'date__lte': end_date,
                'area_lt': 2,
                'is_suspect': True
            }
            request = requests.get(
                self.get_api_url(),
                params=payload,
                timeout=60,
            )
            print(request.url)
            data = request.json()
        except HTTPError as e:
            raise e

        return {
            'max_page': '%d' % (data['count'] / self.limit_per_page),
            'previous_page': int(page) - 1,
            'current_page': page,
            'next_page': int(page) + 1,
            'data': data,
            'total': data['count']
        }
