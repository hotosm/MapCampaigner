from flask_restful import Resource, Api

from campaign_manager import campaign_manager
from campaign_manager.models.campaign import Campaign

api = Api(campaign_manager)


class CampaignList(Resource):
    """Shows a list of all campaigns"""

    def get(self):
        """Get all campaigns.
        """
        campaigns = Campaign.all()
        campaigns_json = []

        for campaign in campaigns:
            campaigns_json.append(campaign.json())

        return campaigns_json


class CampaignNearestList(Resource):
    """Show a list of nearest campaigns"""
    def get(self, coordinate):
        """Get all nearest campaigns.
        
        :param coordinate: coordinate of user e.g. -4.1412,1.412
        :type coordinate: str.
        """
        campaigns = Campaign.nearest_campaigns(coordinate)
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

    def get(self, tag):
        """Get all campaigns.
        
        :param tag: tag to filter
        :type tag: str
        """
        campaigns = Campaign.all(**{
                'tags': tag
        })
        campaigns_json = []

        for campaign in campaigns:
            campaigns_json.append(campaign.json())

        return campaigns_json


# Setup the Api resource routing here
api.add_resource(CampaignList, '/campaigns')
api.add_resource(CampaignTagList, '/campaigns/<string:tag>')
api.add_resource(CampaignNearestList, '/nearest_campaigns/<string:coordinate>')
api.add_resource(CampaignNearestWithTagList, '/nearest_campaigns/<string:coordinate>/<string:tag>')

