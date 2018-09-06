import sys
sys.path.insert(0, "dependencies")
from utilities import (
    build_diff_query,
    build_query,
    build_path,
    post_request,
    save_to_s3
)
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info('got event{}'.format(event))
    uuid = event['campaign_uuid']
    feature = event['feature']
    date = event['date']

    query = '{diff_query}{query}'.format(
        diff_query=build_diff_query(date),
        query=build_query(uuid, feature))

    post_request(query, feature)

    save_to_s3(
        path=build_path(uuid, feature),
        feature=feature)

    # invoke_process_mapper_engagement(uuid, feature)
