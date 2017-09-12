__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '12/09/17'
from campaign_manager.models.campaign import Campaign


def generate_geometry():
    for campaign in Campaign.all('all'):
        geojson_path = Campaign.get_geojson_file(campaign.uuid)
        if not geojson_path:
            campaign.save(save_to_git=False)
