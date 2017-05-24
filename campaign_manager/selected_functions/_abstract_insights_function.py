__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

import os
import json
from abc import ABCMeta
from flask import render_template
from jinja2.exceptions import TemplateNotFound
from campaign_manager.provider import get_osm_data


class AbstractInsightsFunction(object):
    """
    Abstract class insights function.
    """
    __metaclass__ = ABCMeta

    CATEGORIES = ['coverage', 'quality', 'error', 'engagement']
    FEATURES = ['buildings', 'roads']
    FEATURES_MAPPING = {
        'buildings': 'building',
        'roads': 'road'
    }
    EXTRA_MAPPING = {
        'amenity': 'building'
    }
    _function_data = None
    _function_raw_data = None

    function_name = None
    campaign = None

    feature = None
    required_attributes = ""
    category = []

    # attribute of insight function
    need_feature = True
    need_required_attributes = True

    def __init__(self, campaign, feature=None, required_attributes=None):
        self.campaign = campaign
        if not self.feature:
            self.feature = feature
        self.required_attributes = required_attributes

    def name(self):
        """Name of insight functions
        :return: string of name
        """
        name = self.function_name
        if self.feature:
            name = '%s - feature:%s' % (name, self.feature)
            if self.required_attributes:
                name = '%s - attributes:%s' % (name, self.required_attributes)
        return name

    def run(self):
        """Process this function"""
        self._function_raw_data = self._call_function_provider()
        self._function_data = self._process_data(self._function_raw_data)
        self._function_data = self.post_process_data(self._function_data)

    def metadata(self):
        """ Return metadata of data from collected data.
        :return: Metadata of data from collected data.
        """
        if not self._function_raw_data:
            self.run()

        if 'elements' not in self._function_raw_data:
            return {}

        return {
            'collected_data_count': len(self._function_raw_data['elements']),
            'filtered_data_count': len(self._function_data)
        }

    def get_function_data(self):
        """ Return function data
        :return: function data
        :rtype: dict
        """
        return self._function_data

    def post_process_data(self, data):
        """ Process data regarding output.
        This needed for processing data for counting or grouping.

        :param data: Data that received from open street map
        :type data: dict

        :return: Processed data
        :rtype: dict
        """
        return data

    def _call_function_provider(self):
        """ Get required attrbiutes for function provider.
        :return: list of required attributes
        :rtype: [str]
        """
        if self.feature:
            coordinates = self.campaign.geometry['features'][0]
            coordinates = coordinates['geometry']['coordinates'][0]
            correct_coordinates = []
            for coordinate in coordinates:
                correct_coordinates.append(
                    [coordinate[1], coordinate[0]]
                )
            return get_osm_data(
                self.FEATURES_MAPPING[self.feature],
                correct_coordinates)
        else:
            return []

    def _process_data(self, raw_datas):
        """ Get geometry of campaign.
        :param raw_datas: Raw data that returns by function provider
        :type raw_datas: dict

        :return: processed data
        :rtype: dict
        """
        processed_data = []
        required_attributes = {}
        # parsing attributes
        if self.required_attributes:
            for required_attribute in self.required_attributes.split(';'):
                attrs = required_attribute.split('=')
                required_attributes[attrs[0].strip()] = None
                if len(attrs) > 1:
                    attrs[1] = attrs[1].strip()
                    if attrs[1]:
                        required_attributes[attrs[0].strip()] = [
                            value.lower() for value in attrs[1].split(',')
                            ]

        # process data based on required attributes
        if raw_datas:
            req_attr = required_attributes
            if 'elements' not in raw_datas:
                return processed_data

            for raw_data in raw_datas['elements']:
                if 'tags' in raw_data:
                    raw_attr = raw_data["tags"]
                    # just get required attr
                    if len(req_attr) > 0:
                        is_fullfilling_requirement = True
                        clean_data = {}
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
                            clean_data[req_key] = raw_value
                        if is_fullfilling_requirement:
                            processed_data.append(clean_data)
                    else:
                        processed_data.append(raw_attr)
        return processed_data

    # -------------------------------------------------------------
    # HTML SECTION
    # -------------------------------------------------------------
    def get_ui_html_file(self):
        """ Get ui name in templates
        :return: string name of html
        :rtype: str
        """
        raise NotImplementedError()

    def get_summary_html_file(self):
        """ Get summary name in templates
        :return: string name of html
        :rtype: str
        """
        raise NotImplementedError()

    def get_details_html_file(self):
        """ Get summary name in templates
        :return: string name of html
        :rtype: str
        """
        raise NotImplementedError()

    def _get_html(self, ui_type, html_name):
        """preprocess for get html function
        :param html_name: html name that need to be processed
        :type html_name: str

        :return: clean html name
        :rtype: str
        """
        if not self._function_data:
            self.run()

        # return if html_name is None
        if not html_name and html_name != '':
            return ''

        html_name = html_name.replace('.html', '')
        print(self._function_data)
        try:
            return render_template(
                'campaign_widget/%s/%s.html' % (ui_type, html_name),
                **{'data': self._function_data}
            )
        except TemplateNotFound:
            return render_template(
                'campaign_widget/widget_not_found.html')

    def get_ui_html(self):
        """Return ui in html format"""
        return self._get_html('ui', self.get_ui_html_file())

    def get_summary_html(self):
        """Return summary in html format"""
        return self._get_html('summary', self.get_ui_html_file())

    def get_details_html(self):
        """Return details in html format"""
        return self._get_html('details', self.get_ui_html_file())
