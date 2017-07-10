from urllib.request import urlopen
# noinspection PyPep8Naming
from urllib.error import HTTPError
from urllib.request import Request
from reporter import LOGGER


class TaskingManagerProvider(object):
    """Call tasking manager api, and returns the data."""

    api_url = 'http://tasking-manager-staging.eu-west-1.elasticbeanstalk.com' \
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
        self.api_url += 'search?'

        self.api_url += 'page=' + page + '&'

        if search_text:
            self.api_url += 'textSearch=' + search_text + '&'

        if mapper_level:
            self.api_url += 'mapperLevel=' + mapper_level + '&'

        if mapping_types:
            self.api_url += 'mappingTypes=' + mapping_types + '&'

        if organisation_tag:
            self.api_url += 'organisationTag=' + organisation_tag + '&'

        if campaign_tag:
            self.api_url += 'campaignTag=' + campaign_tag + '&'

        web_request = Request(self.api_url, None, self.headers)

        try:
            url_handle = urlopen(web_request, timeout=60)
            data = url_handle.read().decode('utf-8')
            return data
        except HTTPError as e:
            LOGGER.exception('Error with Overpass')
            return e.msg
