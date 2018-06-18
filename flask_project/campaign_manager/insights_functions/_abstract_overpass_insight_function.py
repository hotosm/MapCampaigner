__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

import json
import ast
from abc import ABCMeta
from campaign_manager.insights_functions._abstract_insights_function import (
    AbstractInsightsFunction
)

from campaign_manager.data_providers.overpass_provider import OverpassProvider
from campaign_manager.models.models import *


class AbstractOverpassInsightFunction(AbstractInsightsFunction):
    __metaclass__ = ABCMeta
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
            self.feature_type = additional_data['type']

    def name(self):
        """Name of insight functions
        :return: string of name
        """
        name = self.function_name

        # Feature type is based on additional data that used
        # for example if insight is for Healthsites Facilities
        # than feature type is Healthsites Facilities

        if self.feature_type:
            name = '%s for %s' % (name, self.feature_type)
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
            coordinates = session.query(
                TaskBoundary.coordinates.ST_AsGeoJSON()
                ).filter(
                TaskBoundary.campaign_id == self.campaign.id
                ).first()
            coordinates = ast.literal_eval(coordinates[0])
            coordinates = coordinates['coordinates'][0]
            overpass_data = OverpassProvider().get_data(
                coordinates,
                feature_key=feature_key,
                feature_values=feature_values
            )
        else:
            feature_key = features[0]
            coordinates = session.query(
                TaskBoundary.coordinates.ST_AsGeoJSON()
                ).filter(
                TaskBoundary.campaign_id == self.campaign.id
                ).first()
            coordinates = ast.literal_eval(coordinates[0])
            coordinates = coordinates['coordinates'][0]
            overpass_data = OverpassProvider().get_data(
                coordinates,
                feature_key=feature_key,
            )
        self.last_update = overpass_data['last_update']
        self.is_updating = overpass_data['updating_status']
        return overpass_data['features']
