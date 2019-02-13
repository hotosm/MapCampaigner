import os
import json
from unittest import TestCase
from campaign_manager.aws import S3Data
import requests
from campaign_manager.models.campaign import Campaign


# get the MAPBOX_TOKEN from AWS Beanstalk settings.
MAPBOX_TOKEN = ''


# cd flask_project/campaign_manager/test
# nosetests campaign_manager.test.test_thumbnail
class TestGenerateThumbnail(TestCase):
    def setUp(self):
        # set APP_SETTINGS to 'app_config.AWSProductionConfig'
        # if you want to fetch a campaign in production
        os.environ['APP_SETTINGS'] = 'app_config.AWSStagingConfig'
        os.environ['MAPBOX_TOKEN'] = MAPBOX_TOKEN

    def runTest(self):
        campaign = Campaign('')
        url = campaign.generate_static_map_url(simplify=False)
        print(url)

        request = requests.get(url, stream=True)
        self.assertEqual(request.status_code, 200)
