# coding=utf-8
import unittest
from unittest import mock
from campaign_manager.insights_functions.feature_attribute_completeness \
    import FeatureAttributeCompleteness
from campaign_manager.test.helpers import CampaignObjectTest


class FeatureAttributeCompletenessTestCase(unittest.TestCase):
    """Test function for feature attribute completeness insight function."""

    def setUp(self):
        """Constructor."""
        self.campaign = CampaignObjectTest()
        self.feature_completeness = \
            FeatureAttributeCompleteness(campaign=self.campaign)

    def tearDown(self):
        """Destructor."""
        pass

    def test_get_ui_html_file(self):
        ui_html = self.feature_completeness.get_ui_html_file()
        self.assertEquals(ui_html, 'feature_completeness')

    def test_get_summary_html_file(self):
        self.feature_completeness.get_summary_html_file = \
            mock.MagicMock(return_value='html summary test')
        summary_result = self.feature_completeness.get_summary_html_file
        self.assertIsNotNone(summary_result)
        self.assertEquals(summary_result.return_value, 'html summary test')

    def test_details_html_file(self):
        self.feature_completeness.get_details_html_file = \
            mock.MagicMock(return_value='html details test')
        details_result = self.feature_completeness.get_details_html_file
        self.assertIsNotNone(details_result)
        self.assertEquals(details_result.return_value, 'html details test')

    def test_post_process_data(self):
        self.feature_completeness.post_process_data = \
            mock.MagicMock(return_value='processed data')
        output = self.feature_completeness.post_process_data()
        self.assertEquals(output,'processed data')
