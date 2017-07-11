__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

from campaign_manager.insights_functions._abstract_insights_function import (
    AbstractInsightsFunction
)
from campaign_manager.data_providers.overpass_provider import OverpassProvider


class FeatureAttributeCompleteness(AbstractInsightsFunction):
    function_name = "Showing feature completeness"
    category = ['quality']
    need_required_attributes = True
    icon = 'list'
    _function_good_data = None  # cleaned data

    last_update = ''
    is_updating = False

    def get_ui_html_file(self):
        """ Get ui name in templates
        :return: string name of html
        :rtype: str
        """
        return "feature_completeness"

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

    def get_data_from_provider(self):
        """ Get data provider function
        :return: data from provider
        :rtype: dict
        """
        overpass_data = OverpassProvider().get_data(
                self.FEATURES_MAPPING[self.feature],
                self.campaign.corrected_coordinates()
        )
        self.last_update = overpass_data['last_update']
        self.is_updating = overpass_data['updating_status']
        return overpass_data['features']

    def process_data(self, raw_datas):
        """ Get geometry of campaign.
        :param raw_datas: Raw data that returns by function provider
        :type raw_datas: dict

        :return: processed data
        :rtype: dict
        """
        self._function_good_data = []
        processed_data = []
        required_attributes = self.get_required_attributes()

        for raw_data in raw_datas:

            good_data = False

            if 'tags' not in raw_data:
                continue

            raw_attr = raw_data["tags"]

            for key, values in required_attributes.items():
                tags_needed = raw_attr.get(key, None)

                if tags_needed and tags_needed in [x.lower() for x in values]:
                    good_data = True

            if good_data:
                # Check feature completeness
                self.check_feature_completeness(raw_data)
                self._function_good_data.append(raw_data)

                if not raw_data['error']:
                    processed_data.append(raw_data)

        return processed_data

    def check_feature_completeness(self, feature_data):
        """Check feature completeness.

        :param feature_data: Feature data
        :type feature_data: dict
        """
        error_found = False
        error_message = ''

        # Check name tags
        if 'name' not in feature_data['tags']:
            error_found = True
            error_message = 'Name not found'

        feature_data['error'] = error_found
        feature_data['error_message'] = error_message

    def post_process_data(self, data):
        """Process data regarding output.
        This needed for processing data for counting or grouping.

        :param data: Data that received from open street map
        :type data: dict

        :return: Processed data
        :rtype: dict
        """
        required_attributes = {}
        required_attributes.update(self.get_required_attributes())
        percentage = '0.0'
        if len(self._function_good_data) > 0:
            percentage = '%.1f' % (
                (len(data) / len(self._function_good_data)) * 100
            )

        output = {
            'attributes': required_attributes,
            'data': self._function_good_data,
            'percentage': percentage,
            'complete': len(data),
            'total': len(self._function_good_data),
            'last_update': self.last_update,
            'updating': self.is_updating,
        }
        return output
