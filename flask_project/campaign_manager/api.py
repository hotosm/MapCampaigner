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
            campaigns_json.append(campaign.content_json)

        return campaigns_json


class CampaignNearestList(Resource):
    """Show a list of nearest campaigns"""

    def get(self, coordinate):
        """Get all nearest campaigns.
        """
        campaigns = Campaign.nearest_campaigns(coordinate)
        campaigns_json = []

        for campaign in campaigns:
            campaigns_json.append(campaign.content_json)

        return campaigns_json


# Setup the Api resource routing here
api.add_resource(CampaignList, '/campaigns')
api.add_resource(CampaignNearestList, '/nearest_campaigns/<string:coordinate>')
