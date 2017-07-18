from abc import ABCMeta
import datetime
import xml
import calendar
from urllib.error import URLError
from campaign_manager.insights_functions._abstract_insights_function import (
    AbstractInsightsFunction
)
from reporter.exceptions import (
    OverpassTimeoutException,
    OverpassBadRequestException,
    OverpassConcurrentRequestException)
from reporter.utilities import (
    osm_object_contributions,
    split_polygon
)
from reporter.queries import TAG_MAPPING_REVERSE
from reporter.osm import get_osm_file


class AbstractOverpassUserFunction(AbstractInsightsFunction):
    __metaclass__ = ABCMeta
    category = ['engagement']
    icon = 'list'
    _function_good_data = None  # cleaned data

    def get_data_from_provider(self):
        """ Get required attrbiutes for function provider.
        :return: list of required attributes
        :rtype: [str]
        """
        sorted_user_list = []

        if self.feature:
            coordinates = self.campaign.geometry['features'][0]
            coordinates = coordinates['geometry']['coordinates'][0]
            correct_coordinates = []
            for coordinate in coordinates:
                correct_coordinates.append(
                    [coordinate[1], coordinate[0]]
                )
            start_date = calendar.timegm(datetime.datetime.strptime(
                    self.campaign.start_date, '%Y-%m-%d').timetuple()) * 1000
            end_date = calendar.timegm(datetime.datetime.strptime(
                    self.campaign.end_date, '%Y-%m-%d').timetuple()) * 1000
            polygon_string = split_polygon(correct_coordinates)

            try:
                file_handle = get_osm_file(
                        polygon_string,
                        self.feature,
                        'meta',
                        str(start_date),
                        str(end_date),
                        True)
            except OverpassTimeoutException:
                error = 'Timeout, try a smaller area.'
            except OverpassBadRequestException:
                error = 'Bad request.'
            except OverpassConcurrentRequestException:
                error = 'Please try again later, another query is running.'
            except URLError:
                error = 'Bad request.'
            else:
                try:
                    tag_name = ''
                    if '=' in self.feature:
                        tag_name = self.feature.split('=')[0]
                    else:
                        tag_name = TAG_MAPPING_REVERSE[self.feature]
                    sorted_user_list = osm_object_contributions(
                        file_handle,
                        tag_name,
                        start_date,
                        end_date)
                except xml.sax.SAXParseException:
                    error = (
                        'Invalid OSM xml file retrieved. Please try again '
                        'later.')
            return sorted_user_list
        else:
            return []
