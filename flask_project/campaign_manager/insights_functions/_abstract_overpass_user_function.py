from abc import ABCMeta
import re
import io
import time
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
    OverpassConcurrentRequestException,
    OverpassDoesNotReturnData)
from reporter.utilities import (
    osm_object_contributions,
    split_polygon
)
from campaign_manager.data_providers.overpass_provider import OverpassProvider
from reporter.queries import TAG_MAPPING_REVERSE


class AbstractOverpassUserFunction(AbstractInsightsFunction):
    __metaclass__ = ABCMeta
    icon = 'list'
    _function_good_data = None  # cleaned data

    def initiate(self, additional_data):
        """ Initiate function

        :param additional_data: additional data that needed
        :type additional_data:dict
        """
        if 'type' in additional_data:
            self.feature_type = additional_data['type']

    def get_data_from_provider(self):
        """ Get required attrbiutes for function provider.
        :return: dict of user list and update status
        :rtype: dict
        """
        sorted_user_list = []
        last_update = None
        is_updating = False

        if self.feature:
            start_date = calendar.timegm(datetime.datetime.strptime(
                    self.campaign.start_date, '%Y-%m-%d').timetuple()) * 1000
            end_date = calendar.timegm(datetime.datetime.strptime(
                    self.campaign.end_date, '%Y-%m-%d').timetuple()) * 1000

            try:
                features = self.feature.split('=')
                if len(features) == 0:
                    return []
                elif len(features) == 2:
                    feature_key = features[0]
                    feature_values = features[1].split(',')
                    overpass_data = OverpassProvider().get_data(
                        polygon=self.campaign.corrected_coordinates(),
                        overpass_verbosity='meta',
                        feature_key=feature_key,
                        feature_values=feature_values,
                        date_from=str(start_date),
                        date_to=str(end_date),
                        returns_json=False
                    )
                else:
                    feature_key = features[0]
                    overpass_data = OverpassProvider().get_data(
                        polygon=self.campaign.corrected_coordinates(),
                        overpass_verbosity='meta',
                        feature_key=feature_key,
                        date_from=str(start_date),
                        date_to=str(end_date),
                        returns_json=False
                    )
            except OverpassTimeoutException:
                error = 'Timeout, try a smaller area.'
            except OverpassBadRequestException:
                error = 'Bad request.'
            except OverpassConcurrentRequestException:
                error = 'Please try again later, another query is running.'
            except URLError:
                error = 'Bad request.'
            except OverpassDoesNotReturnData:
                error = 'No data from overpass.'
            else:
                try:
                    last_update = overpass_data['last_update']
                    is_updating = overpass_data['updating_status']
                    tag_name = ''
                    if '=' in self.feature:
                        tag_name = self.feature.split('=')[0]
                    else:
                        tag_name = TAG_MAPPING_REVERSE[self.feature]
                    if isinstance(overpass_data['file'], io.IOBase):
                        sorted_user_list = osm_object_contributions(
                            overpass_data['file'],
                            tag_name,
                            start_date,
                            end_date)
                except xml.sax.SAXParseException:
                    error = (
                        'Invalid OSM xml file retrieved. Please try again '
                        'later.')
            if not last_update:
                last_update = datetime.datetime.now().strftime(
                    '%Y-%m-%d %H:%M:%S')
            return {
                'user_list': sorted_user_list,
                'last_update': last_update,
                'is_updating': is_updating
            }
        else:
            return []
