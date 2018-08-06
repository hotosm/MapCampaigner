import os
from unittest import TestCase
from campaign_manager.aws import S3Data


class TestS3Data(TestCase):
    def setUp(self):
        self.uuid = 'ff6ff8fcfdd847c48dd1bc3c9107b397'
        self.s3_data = S3Data()

    def test_s3_bucket(self):
        """
        The AWS bucket should be configured properly.
        """
        if os.environ.get('ON_TRAVIS', 'false') == 'true':
            self.assertEqual(self.s3_data.bucket,
                'hotosm-fieldcampaigner-data-test')
        else:
            self.assertEqual(self.s3_data.bucket,
                'fieldcampaigner-data-test')

    def test_fetch_campaign_json_file(self):
        """
        It should return a json file from a campaign uuid.
        """
        campaign_json_file = 'campaign/{}.json'.format(self.uuid)
        json = self.s3_data.fetch(campaign_json_file)
        self.assertEqual(json['uuid'], self.uuid)

    def test_fetch_unknown_campaign_json_file(self):
        """
        It should return nothing when fetching an unknown campaign json file.
        """
        campaign_json_file = 'campaign/unknown.json'
        json = self.s3_data.fetch(campaign_json_file)
        self.assertEqual(json, [])

    def test_fetch_campaign_geojson_file(self):
        """
        It should return a geojson file from a campaign uuid.
        """
        campaign_geojson_file = 'campaign/{}.geojson'.format(self.uuid)
        geojson = self.s3_data.fetch(campaign_geojson_file)
        self.assertEqual(geojson['type'], 'FeatureCollection')

    def test_fetch_survey_building_yaml_file(self):
        """
        It should return a YAML survey file.
        """
        survey_file = 'surveys/buildings'
        survey = self.s3_data.fetch(survey_file)
        self.assertEqual(survey['feature'], 'building')

    def test_fetch_unknown_survey_yaml_file(self):
        """
        It should return nothing when fetching an unknown survey file.
        """
        survey_file = 'surveys/unknown'
        survey = self.s3_data.fetch(survey_file)
        self.assertEqual(survey, [])

    def test_is_json_file(self):
        """
        It should return True or False wether the file is json/geojson or not.
        """
        campaign_json_file = 'campaign/{}.json'.format(self.uuid)
        self.assertTrue(self.s3_data.is_json(campaign_json_file))

        campaign_geojson_file = 'campaign/{}.geojson'.format(self.uuid)
        self.assertTrue(self.s3_data.is_json(campaign_geojson_file))

        survey_file = 'surveys/buildings'
        self.assertFalse(self.s3_data.is_json(survey_file))

    def test_list_campaigns(self):
        """
        It should return a list of keys starting with the prefix 'campain'.
        """
        campaigns = self.s3_data.list('campaign')
        self.assertEqual(len(campaigns), 2)
        self.assertEqual(campaigns[0], '{}.geojson'.format(self.uuid))
        self.assertEqual(campaigns[1], '{}.json'.format(self.uuid))

    def test_list_surveys(self):
        """
        It should return a list of keys starting with the prefix 'surveys'.
        """
        surveys = self.s3_data.list('surveys')
        self.assertEqual(len(surveys), 7)
        self.assertEqual(surveys[0], 'buildings')

    def test_list_nothing(self):
        """
        It should return an empty array.
        """
        nothing = self.s3_data.list('nothing')
        self.assertEqual(nothing, [])

    def test_fetch_allowed_managers(self):
        """
        It should fetch the allowed managers file as text.
        """
        managers_file = 'managers.txt'
        content = self.s3_data.fetch(managers_file)
        self.assertEqual('pierrealix' in content, True)

    def test_create_campaign_file(self):
        """
        It should create a campaign json file in s3.
        """
        campaign_body = '{"campaign_creator": "pierrealixt"}'
        self.s3_data.create(
            'campaign/test_campaign.json',
            campaign_body)
        content = self.s3_data.fetch('campaign/test_campaign.json')
        self.assertEqual(content['campaign_creator'], 'pierrealixt')
        self.s3_data.delete('campaign/test_campaign.json')

    def test_delete_coverage_folder(self):
        """
        It should delete a folder.
        """
        # create a file in a folder: coverage/uuid/uuid.shp
        coverage_folder = 'coverage/{}'.format(self.uuid)
        shapefile = '{}/{}.shp'.format(coverage_folder, self.uuid)
        self.s3_data.create(shapefile, 'I am a shapefile, howzit?')

        self.s3_data.delete_folder(coverage_folder)
        shapefile_content = self.s3_data.fetch(shapefile)
        self.assertEqual(shapefile_content, [])

    def test_get_last_modified_date(self):
        """
        It should return a DateTime.
        """
        from datetime import datetime
        last_modified = self.s3_data.get_last_modified_date(
            'campaign/{}.json'.format(self.uuid))
        self.assertTrue(isinstance(last_modified, datetime))
