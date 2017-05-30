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


class MapperEngagement(AbstractInsightsFunction):
    function_name = "Show length of mapper engagement"
    category = ['engagement']
    need_feature = True
    need_required_attributes = False

    def get_ui_html_file(self):
        """ Get ui name in templates
        :return: string name of html
        :rtype: str
        """
        return "mapper_engagement"

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

    def _call_function_provider(self):
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
                    sorted_user_list = osm_object_contributions(
                        file_handle,
                        TAG_MAPPING_REVERSE[self.feature],
                        start_date,
                        end_date)
                except xml.sax.SAXParseException:
                    error = (
                        'Invalid OSM xml file retrieved. Please try again '
                        'later.')
            return sorted_user_list
        else:
            return []

    def run(self):
        """Process this function"""
        self._function_raw_data = self._call_function_provider()
        self._function_data = self.post_process_data(self._function_raw_data)

    def post_process_data(self, data):
        """ Process data regarding output.
        This needed for processing data for counting or grouping.

        :param data: Data that received from open street map
        :type data: dict

        :return: Processed data
        :rtype: dict
        """
        return data
