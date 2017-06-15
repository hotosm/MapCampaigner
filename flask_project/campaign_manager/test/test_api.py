from unittest import TestCase, mock
from campaign_manager.api import (
    CampaignList,
    CampaignNearestList,
    CampaignTagList
)
from campaign_manager.models.campaign import Campaign


def mock_get_campaign():
    campaign = Campaign()
    campaign.uuid = '111'
    campaign.name = 'test'
    campaign._content_json = {
        'name': campaign.name,
        'uuid': campaign.uuid
    }
    return [campaign]


def mock_get_nearest_campaign(coordinate):
    campaign = Campaign()
    campaign.uuid = '111'
    campaign.name = 'test'
    campaign._content_json = {
        'name': campaign.name,
        'uuid': campaign.uuid
    }
    return [campaign]


def mock_get_campaigns_with_tag(tag):
    campaign = Campaign()
    campaign.uuid = '111'
    campaign.name = 'test'
    campaign._content_json = {
        'name': campaign.name,
        'uuid': campaign.uuid
    }
    return [campaign]


class TestApi(TestCase):
    """Test campaign_manager api."""

    def setUp(self):
        """Constructor."""
        pass

    def tearDown(self):
        """Destructor."""
        pass

    @mock.patch('campaign_manager.api.CampaignList.get',
                side_effect=mock_get_campaign)
    def test_campaign_list(self, mock_get_campaign):
        """Test we get all campaign list."""
        campaigns = CampaignList().get()
        self.assertEqual(len(campaigns), 1)
        self.assertEqual(campaigns[0].name, 'test')

    @mock.patch('campaign_manager.api.CampaignNearestList.'
                'get_nearest_campaigns',
                side_effect=mock_get_nearest_campaign)
    def test_get_nearest_campaign(self, mock_get_nearest_campaign):
        """Test get all nearest campaign."""
        coordinate = ''
        campaigns = CampaignNearestList().get_nearest_campaigns(coordinate)
        self.assertEqual(len(campaigns), 1)
        self.assertEqual(campaigns[0].name, 'test')

    @mock.patch('campaign_manager.api.CampaignTagList.'
                'get_campaigns',
                side_effect=mock_get_campaigns_with_tag)
    def test_get_campaign_with_tag(self, mock_get_campaigns_with_tag):
        """Test get all nearest campaign."""
        tag = 'tag'
        campaigns = CampaignTagList().get(tag)
        self.assertEqual(len(campaigns), 1)
        self.assertEqual(campaigns[0]['name'], 'test')
