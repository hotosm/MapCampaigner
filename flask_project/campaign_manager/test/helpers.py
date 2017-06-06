# coding=utf-8

import os
from campaign_manager.utilities import module_path
from campaign_manager.models.json_model import JsonModel


class CampaignObjectTest(JsonModel):
    uuid = 'testcampaign'
    name = 'test'
    campaign_creator = 'anita'
    campaign_status = 'start'
    coverage = {"last_uploader": "anita", "last_uploaded": "2017-06-06"}
    geometry = None
    start_date = None
    end_date = None
    campaign_managers = []
    selected_functions = []
    tags = []
    description = 'campaign object test'

    def get_coverage_folder(self):
        """ Return coverage folder for this campaign
        :return: path for coverage folder
        :rtype: str
        """
        return os.path.join(
            module_path(),
            'test',
            'test_data',
            'coverage',
            self.uuid
        )
