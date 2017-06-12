__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '12/06/17'

import json
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from campaign_manager.data_providers._abstract_data_provider import (
    AbstractDataProvider
)


class OsmchaChangesetProvider(AbstractDataProvider):
    """Data from osmcha"""
    limit_per_page = 15
    osmcha_api_url = (
        "http://osmcha-django-staging.tilestream.net/api/v1/",
        "changesets/?page=%(PAGE)s&page_size=%(LIMIT_PER_PAGE)s&in_bbox=%(BBOX)s",
        "&date__gte=%(START_DATE)s&date__lte=%(END_DATE)s")

    def get_data(self, bbox, page=1, start_date='', end_date=''):
        """Get data from osmcha.
        :param bbox: geometry that used by osmcha
        :type bbox: [4]

        :param page: page that used by osmcha
        :type page: int

        :param start_date: start_date that used by osmcha
        :type start_date: str

        :param end_date: end_date that used by osmcha
        :type end_date: str

        :returns: A data from osmcha
        :rtype: dict
        """
        url = ''.join(self.osmcha_api_url) % {
            'LIMIT_PER_PAGE': self.limit_per_page,
            'BBOX': ','.join(['%s' % value for value in bbox]),
            'PAGE': page,
            'START_DATE': start_date,
            'END_DATE': end_date
        }
        try:
            url_handle = urlopen(url, timeout=60)
            data = url_handle.read().decode('utf-8')
        except HTTPError as e:
            raise e
        data = json.loads(data)

        return {
            'max_page': '%d' % (data['count'] / self.limit_per_page),
            'previous_page': int(page) - 1,
            'current_page': page,
            'next_page': int(page) + 1,
            'data': data,
        }
