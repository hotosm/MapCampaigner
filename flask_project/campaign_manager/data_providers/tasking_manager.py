from urllib.request import urlopen
# noinspection PyPep8Naming
from urllib.error import HTTPError
from urllib.request import Request
from reporter import LOGGER


class TaskingManagerProvider(object):
    """Call tasking manager api, and returns the data."""

    api_url = 'http://tm3.hotosm.org' \
              '/api/v1/project/'
    headers = {'Accept-Language': 'en'}

    def search_project(
            self,
            page,
            search_text=None,
            mapper_level=None,
            mapping_types=None,
            organisation_tag=None,
            campaign_tag=None
    ):
        url_request = self.api_url
        url_request += 'search?'

        url_request += 'page=' + page + '&'

        if search_text:
            url_request += 'textSearch=' + search_text + '&'

        if mapper_level:
            url_request += 'mapperLevel=' + mapper_level + '&'

        if mapping_types:
            url_request += 'mappingTypes=' + mapping_types + '&'

        if organisation_tag:
            url_request += 'organisationTag=' + organisation_tag + '&'

        if campaign_tag:
            url_request += 'campaignTag=' + campaign_tag + '&'

        url_request = url_request.replace(' ', '%20')
        return self.request_data(url_request)

    def project_detail(self, project_id):
        url_request = self.api_url
        url_request += project_id
        return self.request_data(url_request)

    def request_data(self, url_request):
        web_request = Request(url_request, None, self.headers)
        try:
            url_handle = urlopen(web_request, timeout=60)
            data = url_handle.read().decode('utf-8')
            return data
        except HTTPError as e:
            LOGGER.exception('Error with request')
            return e.msg
