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
        self.coverage = {
            "last_uploader": "anita", "last_uploaded": "2017-06-06"}
        self.start_date = None
        self.end_date = None
        self.campaign_managers = []
        self.selected_functions = []
        self.tags = []
        self.description = 'campaign object test'
        self.geometry = {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "properties": {}, "geometry":
                {"type": "Polygon", "coordinates":
                    [[[20.430364608764652, -34.02157746626568],
                      [20.439076423645023, -34.03064717674483],
                      [20.45040607452393, -34.02506319517012],
                      [20.45040607452393, -34.02349819173851],
                      [20.434269905090336, -34.0185184433697],
                      [20.430364608764652, -34.02157746626568]]]}}]}

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
