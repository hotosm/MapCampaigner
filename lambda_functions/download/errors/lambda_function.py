import sys
sys.path.insert(0, "dependencies")
import json
from utilities import (
    build_query,
    save_to_s3,
    post_request,
    build_path
)
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info('got event{}'.format(event))
    uuid = event['campaign_uuid']
    feature = event['feature']
    

    
    query = build_query(uuid, feature);
    post_request(query, feature)
    save_to_s3(
        path=build_path(uuid, feature),
        feature=feature)

