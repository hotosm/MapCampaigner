__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

import os
import json
from abc import ABCMeta
from flask import render_template
from jinja2.exceptions import TemplateNotFound
from campaign_manager.utilities import module_path
from campaign_manager.provider import get_osm_data


class AbstractInsightsFunction(object):
    """
    Abstract class insights function.
    """
    __metaclass__ = ABCMeta
    function_name = None
    _function_data = None

    def __init__(self, campaign):
        self.campaign = campaign

    def get_required_attributes(self):
        """ Get required attributes for function provider.

        i.e:
        {
            'name':None,
            'access':'public'
            'building':['library', 'theatre']
        }

        Note:
        - It will return just name, building, and amenity
        - Because name is None, it will return all name
        - Because access is public, it will return access = public
        - Because amenity is library and theater, it will return both of it


        :return: dictionary of required attributes
        :rtype: dict
        """
        raise NotImplementedError()

    def get_feature(self):
        """ Get feature that needed for openstreetmap.

        :param feature: The type of feature to extract:
            buildings, building-points, roads, potential-idp, boundary-[1,11]
        :type feature: str
        """
        raise NotImplementedError()

    def run(self):
        """Process this function"""
        raw_data = self._call_function_provider()
        self._function_data = self._process_data(raw_data)
        self._function_data = self.post_process_data(self._function_data)

    def get_function_data(self):
        """ Return function data
        :return: function data
        :rtype: dict
        """
        return self._function_data

    def _process_data(self, raw_datas):
        """ Get geometry of campaign.
        :param raw_datas: Raw data that returns by function provider
        :type raw_datas: dict

        :return: processed data
        :rtype: dict
        """
        processed_data = []
        req_attr = self.get_required_attributes()
        if not isinstance(req_attr, dict):
            req_attr = {}
        if 'elements' not in raw_datas:
            return processed_data

        for raw_data in raw_datas['elements']:
            if raw_data['type'] == 'relation' and 'tags' in raw_data:
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
                            req_value = req_value.lower() \
                                if req_value else req_value

                            # check if has same value
                            if req_value and raw_value != req_value:
                                is_fullfilling_requirement = False
                                break
                        else:
                            is_fullfilling_requirement = False
                            break
                        clean_data[req_key] = raw_value
                    if is_fullfilling_requirement:
                        processed_data.append(clean_data)
                else:
                    processed_data.append(raw_data)
        return processed_data

    def post_process_data(self, data):
        """ Process data regarding output.
        This needed for processing data for counting or grouping.

        :param data: Data that received from open street map
        :type data: dict

        :return: Processed data
        :rtype: dict
        """
        return data

    def _get_geometry(self):
        """ Get geometry of campaign.
        :return: geometry
        :rtype: [str]
        """
        return self.campaign.geometry

    def _call_function_provider(self):
        """ Get required attrbiutes for function provider.
        :return: list of required attributes
        :rtype: [str]
        """
        # coordinates = self.campaign.geometry['features'][0]
        # coordinates = coordinates['geometry']['coordinates'][0]
        # correct_coordinates = []
        # for coordinate in coordinates:
        #     correct_coordinates.append(
        #         [coordinate[1], coordinate[0]]
        #     )
        # return get_osm_data(self.get_feature(), correct_coordinates)
        # ---------------------------------------------------
        # DUMMY
        # ---------------------------------------------------
        json_path = os.path.join(
            module_path(), 'dummy_data'
        )
        _file = open(json_path, 'r')
        content = _file.read()
        return json.loads(content)

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
        try:
            return render_template(
                'campaign_widget/%s/%s.html' % (ui_type, html_name),
                **self._function_data)
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
