import os
import json
from unittest import TestCase
from campaign_manager.aws import S3Data
import requests
from campaign_manager.models.campaign import Campaign


class TestGenerateThumbnail(TestCase):
    def runTest(self):
        campaign = Campaign('ff6ff8fcfdd847c48dd1bc3c9107b397')
        url = campaign.generate_static_map_url(simplify=False)

        request = requests.get(url, stream=True)
        self.assertEqual(request.status_code, 200)
