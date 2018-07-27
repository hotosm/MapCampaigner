from unittest import TestCase
from campaign_manager.models.campaign import Campaign


class TestCampaign(TestCase):
    def setUp(self):
        self.uuid = 'ff6ff8fcfdd847c48dd1bc3c9107b397'
        self.campaign = Campaign(self.uuid)

    def test_init_campaign(self):
        self.assertEqual(self.campaign.uuid, self.uuid)
