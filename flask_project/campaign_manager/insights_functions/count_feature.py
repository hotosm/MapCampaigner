__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

from campaign_manager.insights_functions._abstract_overpass_insight_function \
    import AbstractOverpassInsightFunction


class CountFeature(AbstractOverpassInsightFunction):
    function_name = "Number of feature in group"

    # attribute of insight function
    need_feature = True

    def get_ui_html_file(self):
        """ Get ui name in templates
        :return: string name of html
        :rtype: str
        """
        return "piechart"

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

        :return: processed data
        :rtype: dict
        """
        processed_data = []
        required_attributes = self.get_required_attributes()

        # process data based on required attributes
        req_attr = required_attributes

        for raw_data in raw_data:
            if 'tags' not in raw_data:
                continue
            processed_data.append(raw_data['tags'])
        return processed_data

    def post_process_data(self, data):
        """ Process data regarding output.
        This needed for processing data for counting or grouping.

        :param data: Data that received from open street map
        :type data: dict

        :return: Processed data
        :rtype: dict
        """
        output = {
            'last_update': self.last_update,
            'updating': self.is_updating,
            'data': {}
        }
        data = data
        for current_data in data:
            group_type = 'unknown'
            group_key = self.feature
            features = self.feature.split('=')
            if len(features) > 0:
                group_key = features[0]
            try:
                group_type = current_data[group_key]
            except KeyError:
                pass

            building_group = u'{group_key} : {group_type}'.format(
                group_key=group_key,
                group_type=group_type.capitalize()
            )

            if building_group not in output['data']:
                output['data'][building_group] = 0
            output['data'][building_group] += 1
        return output
