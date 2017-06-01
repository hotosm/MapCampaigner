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
    icon = 'list'
    _function_good_data = None  # cleaned data

    def get_data_from_provider(self):
        """ Get data provider function
        :return: data from provider
        :rtype: dict
        """
        return OverpassProvider().get_data(
            self.FEATURES_MAPPING[self.feature], self.campaign.corrected_coordinates()
        )

    def process_data(self, raw_datas):
        """ Get geometry of campaign.
        :param raw_datas: Raw data that returns by function provider
        :type raw_datas: dict

        :return: processed data
        :rtype: dict
        """
        good_data = []
        processed_data = []
        required_attributes = self.get_required_attributes()

        # process data based on required attributes
        if raw_datas:
            req_attr = required_attributes

            for raw_data in raw_datas:
                if 'tags' in raw_data:
                    raw_attr = raw_data["tags"]

                    # just get required attr
                    is_fullfilling_requirement = True
                    if len(req_attr) > 0:
                        # checking data
                        for req_key, req_value in req_attr.items():
                            # if key in attr
                            if req_key in raw_attr:
                                raw_value = raw_attr[req_key].lower()
                                if req_value and raw_value not in req_value:
                                    is_fullfilling_requirement = False
                                    break
                            else:
                                is_fullfilling_requirement = False
                                break
                        if is_fullfilling_requirement:
                            processed_data.append(raw_data)
                    else:
                        processed_data.append(raw_attr)

                    if is_fullfilling_requirement:
                        raw_data['error'] = False
                    else:
                        raw_data['error'] = True
                    good_data.append(raw_data)
                else:
                    good_data.append(raw_data)
                    raw_data['error'] = False
        self._function_good_data = good_data
        return processed_data
