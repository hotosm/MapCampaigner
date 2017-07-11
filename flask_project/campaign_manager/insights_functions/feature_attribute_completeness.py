__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

from campaign_manager.insights_functions._abstract_overpass_insight_function \
    import AbstractOverpassInsightFunction


class FeatureAttributeCompleteness(AbstractOverpassInsightFunction):
    function_name = "Showing feature completeness"
    category = ['quality']
    need_required_attributes = True
    icon = 'list'
    _function_good_data = None  # cleaned data

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

    def process_data(self, raw_datas):
        """ Get geometry of campaign.
        :param raw_datas: Raw data that returns by function provider
        :type raw_datas: dict

        :return: list good data
        :rtype: dict
        """
        self._function_good_data = []
        list_good_data = []
        required_attributes = self.get_required_attributes()

        if not raw_datas:
            return []

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
                    list_good_data.append(raw_data)

        return list_good_data

    def check_feature_completeness(self, feature_data):
        """Check feature completeness.

        :param feature_data: Feature data
        :type feature_data: dict
        """
        error_found = False
        warning_message = ''
        error_message = ''

        # Check name tags
        if 'name' not in feature_data['tags']:
            error_found = True
            error_message = 'Name not found'

        # Check operator
        if not error_found:
            if 'operator:type' not in feature_data['tags'] \
               and 'operator' not in feature_data['tags']:
                error_found = True
                error_message = 'Operator not found'

        # Check all uppercase or lowercase
        if not error_found:
            feature_name = feature_data['tags']['name']
            if feature_name.isupper():
                error_found = True
                warning_message = 'Name is all uppercase'
            elif feature_name.islower():
                error_found = True
                warning_message = 'Name is all lowercase'

        # Check mixed case
        if not error_found:
            feature_name = feature_data['tags']['name']
            for index, name in enumerate(feature_name.split()):

                if name[0].islower() and not self.is_string_int(name[0]):
                    # e.g : name of Feature
                    error_found = True
                    warning_message = 'Name is mixed case'
                    break

        feature_data['error'] = error_found
        feature_data['error_message'] = error_message
        feature_data['warning_message'] = warning_message

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
