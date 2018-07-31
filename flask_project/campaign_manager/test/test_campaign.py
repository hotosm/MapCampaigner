from unittest import TestCase, mock
from app import osm_app as app
from campaign_manager.models.campaign import Campaign

class TestCampaign(TestCase):
    def setUp(self):
        self.uuid = '69657d72fc8541b3a3b12b87bdeaec00'
        self.campaign = Campaign(self.uuid)

    def test_init_campaign(self):
        self.assertEqual(self.campaign.uuid, self.uuid)