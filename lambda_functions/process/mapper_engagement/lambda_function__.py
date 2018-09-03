import sys
sys.path.insert(0, "dependencies")
import json
from utilities import (
    fetch_campaign,
    fetch_osm_data,
    osm_object_contributions
)
from aws import S3Data


def lambda_handler(event, context):
    feature = event['attic_filename'].replace('.xml', '')
    feature_key = feature.split('=')[0]

    campaign_path = 'campaigns/{uuid}'.format(
        uuid=event['campaign_uuid'])
    campaign = fetch_campaign(campaign_path)
    print(campaign)
    osm_data = fetch_osm_data(campaign_path, event['attic_filename'])
    
    tag_name = feature_key
    start_date = campaign['start_date']
    end_date = campaign['end_date']
    sorted_user_list = osm_object_contributions(
        osm_data,
        tag_name,
        start_date,
        end_date)    
