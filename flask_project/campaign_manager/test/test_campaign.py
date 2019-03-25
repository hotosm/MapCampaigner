from unittest import TestCase
from campaign_manager.models.campaign import Campaign


class TestCampaign(TestCase):
    def setUp(self):
        self.uuid = 'ff6ff8fcfdd847c48dd1bc3c9107b397'
        self.geojson = {
            'type': 'FeatureCollection',
            'features': [
                {'type': 'Feature', 'properties': {}, 'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[
                        [18.83301325142384, -33.917957926112294],
                        [18.83964098989964, -33.949394851437425],
                        [18.88501189649105, -33.942389226480245],
                        [18.901514858007435, -33.92174670557128],
                        [18.83301325142384, -33.917957926112294]
                        ]]
                    }}
                ]
            }
        self.campaign = Campaign(self.uuid)

    def test_init_campaign(self):
        self.assertEqual(self.campaign.uuid, self.uuid)
        self.campaign.geometry = self.geojson
        self.assertEqual(self.get_area(), 15161857.47277169)
