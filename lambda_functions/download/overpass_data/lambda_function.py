import sys
sys.path.insert(0, "dependencies")
from campaign import Campaign
from utilities import (
    date_to_dict,
    build_query,
    save_to_s3,
    build_path,
    post_request,
    build_payload,
    invoke_process_feature_completeness,
    invoke_process_count_feature,
    invoke_download_attic_data
)
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info('got event{}'.format(event))
    uuid = event['campaign_uuid']
    feature = event['feature']
    
    campaign = Campaign(uuid)
    
    query = build_query(
        polygon=campaign.corrected_coordinates(),
        feature=feature)

    post_request(query, feature)

    save_to_s3(
        path=build_path(uuid, feature),
        feature=feature)

    invoke_process_feature_completeness(uuid, feature)
    invoke_process_count_feature(uuid, feature)

    # date = date_to_dict(campaign.start_date, campaign.end_date)
    # invoke_download_attic_data(
    #     payload=build_payload(uuid, feature, date))
