__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

from campaign_manager.insights_functions._abstract_overpass_insight_function \
    import AbstractOverpassInsightFunction


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
                if raw_data['type'] == 'node':
                    continue

                if 'tags' in raw_data:
                    raw_attr = raw_data["tags"]

                    # just get required attr
                    is_fulfilling_requirement = True
                    if len(req_attr) > 0:
                        # checking data
                        for req_key, req_value in req_attr.items():
                            # if key in attr
                            if req_key in raw_attr:
                                raw_value = raw_attr[req_key].lower()
                                if req_value and raw_value not in req_value:
                                    is_fulfilling_requirement = False
                                    break
                            else:
                                is_fulfilling_requirement = False
                                break
                        if is_fulfilling_requirement:
                            processed_data.append(raw_data)
                    else:
                        processed_data.append(raw_attr)

                    good_data.append(raw_data)
                else:
                    if not self.need_required_attributes:
                        processed_data.append(raw_data)
                    good_data.append(raw_data)
        self._function_good_data = good_data
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
                output['data'][building_group] = 0
            output['data'][building_group] += 1
        return output
