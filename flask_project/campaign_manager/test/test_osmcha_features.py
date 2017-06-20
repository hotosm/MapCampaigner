# coding=utf-8
import unittest
from app_config import Config
from unittest import mock
from campaign_manager.insights_functions.osmcha_features import (
    OsmchaFeatures
)
from campaign_manager.test.helpers import CampaignObjectTest


class OsmchaFeaturesTestCase(unittest.TestCase):
    """Test insight function to show osmcha error."""

    def setUp(self):
        """Constructor."""
        self.campaign = CampaignObjectTest()
        self.osmcha_features = OsmchaFeatures(campaign=self.campaign)

    def tearDown(self):
        """Destructor."""
        pass

    def test_initiate(self):
        self.osmcha_features.initiate({'int': '2'})
        self.assertEquals(self.osmcha_features.current_page, 1)
        self.osmcha_features.initiate({'page': '4'})
        self.assertEquals(self.osmcha_features.current_page, 4)

    def test_get_ui_html_file(self):
        ui_html = self.osmcha_features.get_ui_html_file()
        self.assertEquals(ui_html, 'osmcha_features')

    def test_get_summary_html_file(self):
        self.osmcha_features.get_summary_html_file = \
            mock.MagicMock(return_value='html summary test')
        summary_result = self.osmcha_features.get_summary_html_file
        self.assertIsNotNone(summary_result)
        self.assertEquals(summary_result.return_value, 'html summary test')

    def test_details_html_file(self):
        self.osmcha_features.get_details_html_file = \
            mock.MagicMock(return_value='html details test')
        details_result = self.osmcha_features.get_details_html_file
        self.assertIsNotNone(details_result)
        self.assertEquals(details_result.return_value, 'html details test')

    def test_get_data_from_provider(self):
        self.osmcha_features.get_data_from_provider = mock.MagicMock(
            return_value={'max_page': '7', 'previous_page': '0',
                          'current_page': '1', 'next_page': '2',
                          'data': 'available'})
        bbox_data = self.osmcha_features.get_data_from_provider()
        self.assertIsNotNone(bbox_data)
        self.assertEquals(bbox_data['max_page'], '7')
        self.assertEquals(bbox_data['previous_page'], '0')
        self.assertEquals(bbox_data['current_page'], '1')
        self.assertEquals(bbox_data['next_page'], '2')
        self.assertEquals(bbox_data['data'], 'available')

    def test_process_data(self):
        raw_data = {'data1': '1234', 'data2': '2345'}
        processed_data = self.osmcha_features.process_data(
            raw_data=raw_data)
        raw_data['osmcha_url'] = Config().OSMCHA_FRONTEND_URL
        self.assertEquals(
            raw_data, processed_data)
