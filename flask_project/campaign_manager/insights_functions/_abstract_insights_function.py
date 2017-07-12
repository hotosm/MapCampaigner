__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

from abc import ABCMeta
from flask import render_template
from jinja2.exceptions import TemplateNotFound


class AbstractInsightsFunction(object):
    """
    Abstract class insights function.
    """
    __metaclass__ = ABCMeta

    CATEGORIES = ['coverage', 'quality', 'error', 'engagement']

    _function_raw_data = None  # data exaclty from osm
    _function_data = None  # data that used by others

    icon = 'pie-chart'
    function_name = None
    campaign = None

    feature = None
    required_attributes = ""
    category = []

    manager_only = False
    type_required = False

    def __init__(
            self,
            campaign,
            feature=None,
            required_attributes=None,
            additional_data={}):
        self.campaign = campaign
        if not self.feature:
            self.feature = feature
        self.required_attributes = required_attributes
        self.additional_data = additional_data
        if 'function_id' in additional_data:
            self.function_id = additional_data['function_id']
        self.initiate(additional_data)

    def initiate(self, additional_data):
        """ Initiate function

        :param additional_data: additional data that needed
        :type additional_data:dict
        """
        pass

    def name(self):
        """Name of insight functions
        :return: string of name
        """
        name = self.function_name
        return name

    def run(self):
        """Process this function"""
        self._function_raw_data = self.get_data_from_provider()
        self._function_data = self.process_data(self._function_raw_data)
        self._function_data = self.post_process_data(self._function_data)

    def get_function_data(self):
        """ Return function data
        :return: function data
        :rtype: dict
        """
        return self._function_data

    def get_function_raw_data(self):
        """ Return function raw data
        :return: function raw data
        :rtype: dict
        """
        return self._function_raw_data

    def get_data_from_provider(self):
        """ Get data provider function
        :return: data from provider
        :rtype: dict
        """
        raise NotImplementedError()

    def process_data(self, raw_datas):
        """ Get geometry of campaign.
        :param raw_datas: Raw data that returns by function provider
        :type raw_datas: dict

        :return: processed data
        :rtype: dict
        """
        raise NotImplementedError()

    def post_process_data(self, data):
        """ Process data regarding output.
        This needed for processing data for counting or grouping.

        :param data: Data that received from open street map
        :type data: dict

        :return: Processed data
        :rtype: dict
        """
        return data

    def get_required_attributes(self):
        """Parsing required attributes
        """
        required_attributes = {}
        # parsing attributes
        if self.required_attributes:
            for required_attribute in self.required_attributes.split(';'):
                attrs = required_attribute.split('=')
                if attrs[0]:
                    required_attributes[attrs[0].strip()] = None
                    if len(attrs) > 1:
                        attrs[1] = attrs[1].strip()
                        if attrs[1]:
                            required_attributes[attrs[0].strip()] = [
                                value.lower() for value in attrs[1].split(',')
                                ]
        return required_attributes

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
                **{
                    'data': self._function_data,
                    'function_id': self.function_id,
                    'additional_data': self.additional_data
                }
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
