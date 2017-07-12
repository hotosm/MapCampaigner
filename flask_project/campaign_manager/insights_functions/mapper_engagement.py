from campaign_manager.insights_functions._abstract_overpass_user_function \
    import (
        AbstractOverpassUserFunction
    )


class MapperEngagement(AbstractOverpassUserFunction):
    function_name = "Show length of mapper engagement"
    category = ['engagement']

    def get_ui_html_file(self):
        """ Get ui name in templates
        :return: string name of html
        :rtype: str
        """
        return "mapper_engagement"

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
        return raw_data
