__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '29/05/17'

from urllib import request
from bs4 import BeautifulSoup
from urllib.error import HTTPError, URLError
from campaign_manager.data_providers._abstract_data_provider import (
    AbstractDataProvider
)


class OsmchaProvider(AbstractDataProvider):
    """Data from osmcha"""
    osmcha_url = "https://osmcha.mapbox.com/?bbox=%(BBOX)s&page=%(PAGE)s"

    def beautify(self, html_doc):
        soup = BeautifulSoup(html_doc, 'html.parser')
        return soup

    def get_soup(self, url):
        trying = 0
        html_doc = ''
        while True:
            try:
                html_doc = request.urlopen(url)
                break
            except (HTTPError, URLError):
                trying += 1
                print("connection error, trying again - %d" % trying)
                if trying >= 5:
                    break
        return self.beautify(html_doc)

    def get_data(self, bbox, page=1):
        """Get data from osmcha.
        :param bbox: bbox that used by osmcha
        :type bbox: [4]

        :param page: page that used by osmcha
        :type page: int

        :returns: A data from osmcha
        :rtype: dict
        """
        url = self.osmcha_url % {
            'BBOX': ','.join(['%s' % value for value in bbox]),
            'PAGE': page
        }
        html = self.get_soup(url)
        # get headers
        headers = []
        table_head = html.find("thead")
        if table_head:
            rows = table_head.findAll("th")
            for row in rows:
                headers.append(row.string)

        # get data
        table_body = html.find("tbody")
        data = []
        if table_body:
            # get rows
            rows = table_body.findAll("tr")
            for row in rows:
                cells = row.findAll("td")
                json = {}
                for index, value in enumerate(headers):
                    json[value] = cells[index]
                data.append(json)

        pagination = html.find("p", {'class', 'text-pagination'})
        max_page = pagination.string.strip().split('of')[1]
        max_page = max_page.strip()

        return {
            'max_page': max_page,
            'previous_page': int(page) - 1,
            'current_page': page,
            'next_page': int(page) + 1,
            'data': data,
        }
