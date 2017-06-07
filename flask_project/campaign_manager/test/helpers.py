# coding=utf-8

import os
from campaign_manager.utilities import module_path
from campaign_manager.models.campaign import Campaign


class CampaignObjectTest(Campaign):

    def __init__(self):
        self.uuid = 'testcampaign'
        self.name = 'test'
        self.campaign_creator = 'anita'
        self.campaign_status = 'start'
        self.coverage = {"last_uploader": "anita", "last_uploaded": "2017-06-06"}
        self.geometry = None
        self.start_date = None
        self.end_date = None
        self.campaign_managers = []
        self.selected_functions = []
        self.tags = []
        self.description = 'campaign object test'

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
