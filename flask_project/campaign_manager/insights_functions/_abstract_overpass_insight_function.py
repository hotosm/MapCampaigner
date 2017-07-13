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
        if self.feature in self.FEATURES_MAPPING:
            self.feature = self.FEATURES_MAPPING[self.feature]
        if 'type' in additional_data:
            self.type = additional_data['type']

    def name(self):
        """Name of insight functions
        :return: string of name
        """
        name = self.function_name
        return name

    def get_data_from_provider(self):
        """ Get data provider function
        :return: data from provider
        :rtype: dict
        """
        features = self.feature.split('=')
        if len(features) == 0:
            return []
        elif len(features) == 2:
            feature_key = features[0]
            feature_values = features[1].split(',')
            overpass_data = OverpassProvider().get_data(
                self.campaign.corrected_coordinates(),
                feature_key=feature_key,
                feature_values=feature_values
            )
        else:
            feature_key = features[0]
            overpass_data = OverpassProvider().get_data(
                self.campaign.corrected_coordinates(),
                feature_key=feature_key,
            )
        self.last_update = overpass_data['last_update']
        self.is_updating = overpass_data['updating_status']
        return overpass_data['features']
