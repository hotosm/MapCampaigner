__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

from abc import ABCMeta
from campaign_manager.insights_functions._abstract_insights_function import (
    AbstractInsightsFunction
)

from campaign_manager.data_providers.overpass_provider import OverpassProvider


class AbstractOverpassInsightFunction(AbstractInsightsFunction):
    __metaclass__ = ABCMeta
    category = ['quality']
    FEATURES_MAPPING = {
        'buildings': 'building',
        'roads': 'road'
    }
    icon = 'list'
    tag = {}

    last_update = ''
    is_updating = False
    type_required = True

    def initiate(self, additional_data):
        """ Initiate function

        :param additional_data: additional data that needed
        :type additional_data:dict
        """
        if 'type' in additional_data:
            try:
                self.tag = self.campaign.types[additional_data['type']]
            except (ValueError, KeyError):
                pass
        if self.feature in self.FEATURES_MAPPING:
            self.feature = self.FEATURES_MAPPING[self.feature]

    def name(self):
        """Name of insight functions
        :return: string of name
        """
        name = self.function_name
        if self.tag:
            name += ' for type %s' % self.tag['type']
        return name

    def get_data_from_provider(self):
        """ Get data provider function
        :return: data from provider
        :rtype: dict
        """
        if not self.tag:
            return []

        value = self.campaign.get_json_type(self.tag['type'])
        feature = value['feature']
        if feature in value['tags']:
            overpass_data = OverpassProvider().get_data(
                self.campaign.corrected_coordinates(),
                feature_key=value['feature'],
                feature_values=value['tags'][feature]
            )
        else:
            overpass_data = OverpassProvider().get_data(
                self.campaign.corrected_coordinates(),
                feature_key=value['feature'],
            )
        self.last_update = overpass_data['last_update']
        self.is_updating = overpass_data['updating_status']
        return overpass_data['features']
