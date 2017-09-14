from flask_restful import Resource, Api
from flask import request
import logging
from flask import current_app

from campaign_manager import campaign_manager
from campaign_manager.models.campaign import Campaign
from campaign_manager.insights_functions.mapper_engagement import \
    MapperEngagement
from campaign_manager.utilities import get_coordinate_from_ip

api = Api(campaign_manager)


class CampaignList(Resource):
    """Shows a list of all campaigns"""

    def get_all_campaign(self, campaign_status, args):
        """Returns all campaign from model.
        """
        return Campaign.all(campaign_status=campaign_status, **args)

    def get(self, campaign_status):
        """Get all campaigns.
        """
        args = request.args
        campaigns = self.get_all_campaign(campaign_status, args)
        campaigns_json = []

        for campaign in campaigns:
            campaigns_json.append(campaign.json())

        return campaigns_json


class CampaignNearestList(Resource):
    """Show a list of nearest campaigns"""
    def get_nearest_campaigns(self, coordinate, campaign_status, args):
        """Returns all nearest campaign.

        :param campaign_status: status of campaign, active or inactive
        :type campaign_status: str

        :param coordinate: coordinate of user e.g. -4.1412,1.412
        :type coordinate: str.
        """
        return Campaign.nearest_campaigns(coordinate, campaign_status, **args)

    def get(self, campaign_status):
        """Get all nearest campaigns.

        :param campaign_status: status of campaign, active or inactive
        :type campaign_status: str
        """
        args = request.args
        if 'lon' in args and 'lat' in args:
            lon = args['lon']
            lat = args['lat']
            coordinate = lat + ',' + lon
        else:
            coordinate = get_coordinate_from_ip()
        campaigns = self.get_nearest_campaigns(
                coordinate,
                campaign_status,
                args
        )
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


class CampaignTotal(Resource):
    """Show total of campaign and participants."""

    def get_campaigns(self):
        """Returns campaigns.
        """
        return Campaign.all(campaign_status='active')

    def get(self):
        """Get total of campaign and participants."""
        campaigns = self.get_campaigns()
        participants_total = 0
        for campaign in campaigns:
            if campaign.total_participants_count:
                participants_total += campaign.total_participants_count

        return {
            'campaign_total': len(campaigns),
            'participant_total': participants_total
        }


class CampaignContributors(Resource):
    """Show Campaign Contributors."""
    feature = None

    def get_campaign(self, uuid):
        """Return campaign."""
        return Campaign(uuid=uuid)

    def get(self, uuid, feature):
        """Get total contributors."""

        campaign = self.get_campaign(uuid)

        user = []

        mapper = MapperEngagement(
            campaign=campaign, feature=feature)
        mapper.run()
        data = mapper.get_function_data()

        for entry in data['user_list']:
            if entry['name'] not in user:
                user.append(entry['name'])

        contributors_total = len(user)

        return {'contributors_total': contributors_total}


# Setup the Api resource routing here
api.add_resource(
        CampaignList,
        '/campaigns/<string:campaign_status>')
api.add_resource(
        CampaignTagList,
        '/campaigns/<string:tag>')
api.add_resource(
        CampaignNearestList,
        '/nearest_campaigns/<string:campaign_status>')
api.add_resource(
        CampaignNearestWithTagList,
        '/nearest_campaigns/<string:coordinate>/<string:tag>')
api.add_resource(
        CampaignTotal,
        '/total_campaigns')
api.add_resource(
        CampaignContributors,
        '/campaign/total_contributors/<string:uuid>/<string:feature>')
