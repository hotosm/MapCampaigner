__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'
from campaign_manager.insights_functions._abstract_overpass_insight_function \
    import (
        AbstractOverpassInsightFunction)


class CountFeature(AbstractOverpassInsightFunction):
    function_name = "Showing number of feature in group"
    category = ['quality']
    need_required_attributes = False

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

    def post_process_data(self, data):
        """ Process data regarding output.
        This needed for processing data for counting or grouping.

        :param data: Data that received from open street map
        :type data: dict

        :return: Processed data
        :rtype: dict
        """
        output = {}
        for current_data in data:
            key = 'building'
            alternative_keys = ['amenity']

            if key not in current_data:
                for alternative in alternative_keys:
                    if alternative in current_data:
                        key = alternative

            try:
                building_type = current_data[key]
            except KeyError:
                building_type = 'unknown'

            building_group = u'{group_key} : {group_type}'.format(
                group_key=key,
                group_type=building_type.capitalize()
            )

            if building_group not in output:
                output[building_group] = 0
            output[building_group] += 1

        return output
