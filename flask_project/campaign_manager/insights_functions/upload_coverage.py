__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

import json
import os
import shutil
from campaign_manager.insights_functions._abstract_insights_function import (
    AbstractInsightsFunction
)
from campaign_manager.data_providers.shapefile_provider import ShapefileProvider


class UploadCoverage(AbstractInsightsFunction):
    function_name = "Upload shapefile for creating coverage"
    category = ['coverage']
    need_feature = False
    need_required_attributes = False
    manager_only = True

    def initiate(self, additional_data):
        """ Initiate function

        :param additional_data: additional data that needed
        :type additional_data:dict
        """
        if self.campaign:
            self.run()

    def get_ui_html_file(self):
        """ Get ui name in templates
        :return: string name of html
        :rtype: str
        """
        return "upload_coverage"

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

    def get_data_from_provider(self):
        """ Get data provider function
        :return: data from provider
        :rtype: dict
        """
        coverage_folder = self.campaign.get_coverage_folder()
        shapefile_file = "%s/%s.shp" % (
            coverage_folder, self.campaign.uuid
        )
        return ShapefileProvider().get_data(
            shapefile_file
        )

    def process_data(self, raw_datas):
        """ Get geometry of campaign.
        :param raw_datas: Raw data that returns by function provider
        :type raw_datas: dict

        :return: processed data
        :rtype: dict
        """
        return raw_datas

    def delete_coverage_files(self):
        """Delete coverage files"""
        coverage_folder = self.campaign.get_coverage_folder()
        if os.path.exists(coverage_folder):
            shutil.rmtree(coverage_folder)

    def get_coverage_files(self):
        """ Get coverage files
        :return: coverage in geojson
        :rtype: []
        """
        coverage_folder = self.campaign.get_coverage_folder()
        output_files = []
        for root, dirs, files in os.walk(coverage_folder):
            for file in files:
                output_files.append(file)
        return output_files

    def post_process_data(self, data):
        """ Process data regarding output.
        This needed for processing data for counting or grouping.

        :param data: Data that received from open street map
        :type data: dict

        :return: Processed data
        :rtype: dict
        """

        output = {
            'uuid': self.campaign.uuid,
            'files': self.get_coverage_files(),
        }
        if self.campaign.coverage:
            output['coverage'] = {
                'last_uploader': self.campaign.coverage['last_uploader'],
                'last_uploaded': self.campaign.coverage['last_uploaded'],
                'geojson': json.dumps(data)
            }
        return output
