# coding=utf-8
import unittest
from unittest import mock
from campaign_manager.insights_functions.upload_coverage import UploadCoverage
from campaign_manager.test.helpers import CampaignObjectTest


class UploadCoverageTestCase(unittest.TestCase):
    """Test the insights function to upload shapefile for creating coverage."""

    def setUp(self):
        """Constructor."""
        self.campaign = CampaignObjectTest()
        self.uuid = self.campaign.uuid
        self.upload_coverage = UploadCoverage(campaign=self.campaign)

    def tearDown(self):
        """Destructor."""
        pass

    def test_initiate(self):
        upload_coverage_test = \
            self.upload_coverage.initiate(additional_data={})
        self.assertIsNotNone(self, upload_coverage_test)

    def test_get_ui_html_file(self):
        ui_html = self.upload_coverage.get_ui_html_file()
        self.assertEquals(ui_html, 'upload_coverage')

    def test_get_summary_html_file(self):
        self.upload_coverage.get_summary_html_file = \
            mock.MagicMock(return_value='html summary test')
        summary_result = self.upload_coverage.get_summary_html_file
        self.assertIsNotNone(summary_result)
        self.assertEquals(summary_result.return_value, 'html summary test')

    def test_details_html_file(self):
        self.upload_coverage.get_details_html_file = \
            mock.MagicMock(return_value='html details test')
        details_result = self.upload_coverage.get_details_html_file
        self.assertIsNotNone(details_result)
        self.assertEquals(details_result.return_value, 'html details test')

    def test_get_data_from_provider(self):
        shapefile_file = self.upload_coverage.get_data_from_provider()
        self.assertIsNotNone(shapefile_file)
        self.assertEquals(shapefile_file['type'], 'FeatureCollection')

    def test_process_data(self):
        process_data = UploadCoverage.process_data(
            self, raw_datas={('data1', 1234), ('data2', 2345)})
        self.assertEquals(process_data, {('data1', 1234), ('data2', 2345)})

    def test_get_coverage_files(self):
        output_files = self.upload_coverage.get_coverage_files()
        expected_output_files = \
            ['%s.dbf' % self.uuid, '%s.prj' % self.uuid, '%s.shp' % self.uuid,
             '%s.qpj' % self.uuid, '%s.shx' % self.uuid]
        self.assertIsNotNone(output_files)
        self.assertEquals(output_files, expected_output_files)

    def test_post_process_data(self):
        post_output = self.upload_coverage.post_process_data(data={})
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
