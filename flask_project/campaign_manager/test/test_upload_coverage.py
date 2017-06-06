# coding=utf-8
import os
import unittest
from campaign_manager.insights_functions.upload_coverage import UploadCoverage
from campaign_manager.utilities import module_path
from campaign_manager.test.helpers import CampaignObjectTest


class UploadCoverageTestCase(unittest.TestCase):
    """Test the insights function to upload shapefile for creating coverage."""

    def setUp(self):
        self.campaign = CampaignObjectTest()
        self.uuid = self.campaign.uuid

    def test_initiate(self):
        self.UploadCoverageTest = \
            UploadCoverage.initiate(self, additional_data={})
        self.assertIsNotNone(self, self.UploadCoverageTest)

    def test_get_ui_html_file(self):
        ui_html = UploadCoverage.get_ui_html_file(self)
        self.assertEquals(ui_html, 'upload_coverage')

    def test_get_summary_html_file(self):
        summary_html = UploadCoverage.get_summary_html_file(self)
        self.assertEquals(summary_html, '')

    def test_details_html_file(self):
        details_html_file = UploadCoverage.get_details_html_file(self)
        self.assertEquals(details_html_file, '')

    def test_get_data_from_provider(self):
        shapefile_file = UploadCoverage.get_data_from_provider(self)
        self.assertIsNotNone(shapefile_file)
        self.assertEquals(shapefile_file['type'], 'FeatureCollection')

    def test_process_data(self):
        process_data = UploadCoverage.process_data(
            self, raw_datas={('data1', 1234), ('data2', 2345)})
        self.assertEquals(process_data, {('data1', 1234), ('data2', 2345)})

    def test_get_coverage_files(self):
        output_files = UploadCoverage.get_coverage_files(self)
        expected_output_files = \
            ['%s.dbf' % self.uuid, '%s.prj' % self.uuid, '%s.shp' % self.uuid,
             '%s.qpj' % self.uuid, '%s.shx' % self.uuid]
        self.assertIsNotNone(output_files)
        self.assertEquals(output_files, expected_output_files)

    def test_post_process_data(self):
        post_output = UploadCoverage.post_process_data(self, data={})
        expected_output_files = \
            ['%s.dbf' % self.uuid, '%s.prj' % self.uuid, '%s.shp' % self.uuid,
             '%s.qpj' % self.uuid, '%s.shx' % self.uuid]
        expected_coverage = \
            {'last_uploader': 'anita',
             'last_uploaded': '2017-06-06', 'geojson': '{}'}
        self.assertIsNotNone(post_output)
        self.assertEquals(post_output['uuid'], self.uuid)
        self.assertEquals(post_output['files'], expected_output_files)
        self.assertEquals(post_output['coverage'], expected_coverage)

    def get_coverage_files(self):
        """ Get coverage files
        :return: coverage in geojson
        :rtype: []
        """
        coverage_folder = os.path.join(
            module_path(),
            'test',
            'test_data',
            'coverage',
            self.uuid
        )
        output_files = []
        for root, dirs, files in os.walk(coverage_folder):
            for file in files:
                output_files.append(file)
        return output_files
