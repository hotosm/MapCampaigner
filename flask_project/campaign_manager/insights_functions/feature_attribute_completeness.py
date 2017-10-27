__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'
import json
from campaign_manager.insights_functions._abstract_overpass_insight_function \
    import AbstractOverpassInsightFunction


class FeatureAttributeCompleteness(AbstractOverpassInsightFunction):
    function_name = "Feature completeness"
    tags_capitalizaition_checks = ['name']
    icon = 'list'
    _function_good_data = None  # cleaned data
    nodes = {}

    # attribute of insight function
    need_feature = True
    need_required_attributes = True

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

    def process_data(self, raw_data):
        """ Get geometry of campaign.
        :param raw_data: Raw data that returns by function provider
        :type raw_data: dict

        :return: list good data
        :rtype: dict
        """
        list_good_data = []
        self._function_good_data = []

        if not raw_data or not self.feature_type:
            return []
        try:
            required_attributes = self.get_required_attributes()
            for value in raw_data:

                if 'tags' not in value:
                    continue

                self._function_good_data.append(value)
                self.check_feature_completeness(
                    value, required_attributes)

                if value['error'] == 'False':
                    list_good_data.append(value)
        except KeyError:
            pass

        return list_good_data

    def check_capitalization(self, key, value):
        # Check all uppercase or lowercase
        if value.isupper():
            return '%s value is all uppercase' % key
        elif value.islower():
            return '%s value is all lowercase' % key

        # Check mixed case
        for index, name in enumerate(value.split()):
            if name[0].islower() and not self.is_string_int(name[0]):
                # e.g : name of Feature
                return '%s value is mixed case' % key

        return None

    def check_feature_completeness(
            self, feature_data, required_attributes):
        """Check feature completeness.

        :param feature_data: Feature data
        :type feature_data: dict

        :param required_attributes: Required attributes
        :type required_attributes: dict
        """
        warning_message = []
        error_message = []

        tags = feature_data['tags']

        if isinstance(required_attributes, str):
            return

        for required_attribute, survey_values in required_attributes.items():
            if required_attribute not in tags:
                error_message.append(
                    '%s not found' % required_attribute)
            else:
                value_in_tag = tags[required_attribute]
                if survey_values:
                    if value_in_tag not in survey_values:
                        error_message.append(
                            '%s is not allowed as value tag' %
                            value_in_tag)
                if required_attribute in self.tags_capitalizaition_checks:
                    warning = self.check_capitalization(
                        required_attribute, value_in_tag)
                    if warning:
                        warning_message.append(warning)

        feature_data['error'] = 'False'
        if warning_message or error_message:
            feature_data['error'] = 'True'

        feature_data['error_message'] = ', '.join(error_message)
        feature_data['warning_message'] = ', '.join(warning_message)
        feature_data['completeness'] = \
            (len(error_message) / len(required_attribute)) * 100

    def is_string_int(self, text):
        """Check whether the text is int or not."""
        try:
            int(text)
        except ValueError:
            return False

        return True

    def post_process_data(self, data):
        """Process data regarding output.
        This needed for processing data for counting or grouping.

        :param data: Data that received from open street map
        :type data: dict

        :return: Processed data
        :rtype: dict
        """
        percentage = '0.0'
        if len(self._function_good_data) > 0:
            percentage = '%.1f' % (
                (len(data) / len(self._function_good_data)) * 100
            )

        output = {
            'attributes': self.get_required_attributes(),
            'data': self._function_good_data,
            'percentage': percentage,
            'complete': len(data),
            'total': len(self._function_good_data),
            'last_update': self.last_update,
            'updating': self.is_updating,
            'raw_data': self.get_function_raw_data()
        }
        return output
