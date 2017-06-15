from flask_restful import Resource, Api

from campaign_manager import campaign_manager
from campaign_manager.models.campaign import Campaign

api = Api(campaign_manager)


class CampaignList(Resource):
    """Shows a list of all campaigns"""

    def get_all_campaign(self):
        """Returns all campaign from model.
        """
        return Campaign.all()

    def get(self):
        """Get all campaigns.
        """
        campaigns = self.get_all_campaign()
        campaigns_json = []

        for campaign in campaigns:
            campaigns_json.append(campaign.json())

        return campaigns_json


class CampaignNearestList(Resource):
    """Show a list of nearest campaigns"""
    def get_nearest_campaigns(self, coordinate):
        """Returns all nearest campaign.

        :param coordinate: coordinate of user e.g. -4.1412,1.412
        :type coordinate: str.
        """
        return Campaign.nearest_campaigns(coordinate)

    def get(self, coordinate):
        """Get all nearest campaigns.

        :param coordinate: coordinate of user e.g. -4.1412,1.412
        :type coordinate: str.
        """
        campaigns = self.get_nearest_campaigns(coordinate)
        campaigns_json = []

        for campaign in campaigns:
            campaigns_json.append(campaign.json())

        return campaigns_json


class CampaignNearestWithTagList(Resource):
    """Show a list of nearest campaigns with tag filter"""

    def get(self, coordinate, tag):
        """Get all nearest campaigns.

        :param coordinate: coordinate of user e.g. -4.1412,1.412
        :type coordinate: str

        :param tag: tag to filter
        :type tag: str
        """
        campaigns = Campaign.nearest_campaigns(coordinate, **{
                'tags': tag
        })
        campaigns_json = []

        for campaign in campaigns:
            campaigns_json.append(campaign.json())

        return campaigns_json


class CampaignTagList(Resource):
    """Shows a list of all campaigns with tag filter"""

    def get_campaigns(self, tag):
        """Returns campaign with tag.

        :param tag: tag to filter
        :type tag: str
        """
        return Campaign.all(**{
                    'tags': tag
                })

    def get(self, tag):
        """Get all campaigns.

        :param tag: tag to filter
        :type tag: str
        """
        campaigns = self.get_campaigns(tag)
        campaigns_json = []

        for campaign in campaigns:
            campaigns_json.append(campaign.json())

        return campaigns_json


# Setup the Api resource routing here
api.add_resource(CampaignList, '/campaigns')
api.add_resource(CampaignTagList, '/campaigns/<string:tag>')
api.add_resource(CampaignNearestList, '/nearest_campaigns/<string:coordinate>')
api.add_resource(
        CampaignNearestWithTagList,
        '/nearest_campaigns/<string:coordinate>/<string:tag>')
