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
    function_data = None

    def __init__(self, campaign):
        self.campaign = campaign

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

    def get_required_attributes(self):
        """ Get required attributes for function provider.
        :return: list of required attributes
        :rtype: [str]
        """
        raise NotImplementedError()

    def process_data(self, raw_data):
        """ Get geometry of campaign.
        :param raw_data: Raw data that returns by function provider
        :type raw_data: dict

        :return: processed data
        :rtype: dict
        """
        raise NotImplementedError()

    def run(self):
        """Process this function"""
        raw_data = self._call_function_provider()
        self.function_data = self.process_data(raw_data)

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
        geometry = self._get_geometry()
        # ---------------------------------
        # here calls function provider
        # ---------------------------------
        return {}

    def _get_html(self, ui_type, html_name):
        """preprocess for get html function
        :param html_name: html name that need to be processed
        :type html_name: str

        :return: clean html name
        :rtype: str
        """
        if not self.function_data:
            self.run()

        # return if html_name is None
        if not html_name and html_name != '':
            return ''

        html_name = html_name.replace('.html', '')
        try:
            return render_template(
                'campaign_widget/%s/%s.html' % (ui_type, html_name),
                **self.function_data)
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
