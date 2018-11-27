import sys
sys.path.insert(0, "dependencies")
from campaign import Campaign
from utilities import (
    date_to_dict,
    build_query,
    save_to_s3,
    save_query,
    build_path,
    build_query_path,
    post_request,
    build_payload,
    invoke_process_feature_completeness,
    invoke_process_count_feature,
    invoke_process_mapper_engagement
)
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info('got event{}'.format(event))
    uuid = event['campaign_uuid']
    type_name = event['type']
    type_id = type_name.replace(' ', '_')

    campaign = Campaign(uuid)

    for type_key in campaign.types:
        if campaign.types[type_key]['type'] == type_name:
            typee = campaign.types[type_key]

    query = build_query(
        polygon=campaign.corrected_coordinates(),
        typee=typee)
    
    save_query(
        path=build_query_path(uuid, type_id),
        query=query)

    
    post_request(query, type_id)

    save_to_s3(
        path=build_path(uuid, type_id),
        type_id=type_id)

    invoke_process_feature_completeness(uuid, type_name)
    invoke_process_count_feature(uuid, type_name)
    invoke_process_mapper_engagement(uuid, type_name)

    # date = date_to_dict(campaign.start_date, campaign.end_date)
    # invoke_download_attic_data(
    #     payload=build_payload(uuid, feature, date))
