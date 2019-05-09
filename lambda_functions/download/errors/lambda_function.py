import sys
sys.path.insert(0, "dependencies")
import json
from utilities import (
    build_query,
    save_to_s3,
    post_request,
    build_path,
    fetch_campaign,
    campaign_path
)
import logging
from aws import S3Data


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    try:
        main(event, context)
    except Exception as e:
        S3Data().create(
            key=f'campaigns/{event["campaign_uuid"]}/failure.json',
            body=json.dumps({'function': 'download_errors', 'failure': str(e)}))


def main(event, context):
    logger.info('got event{}'.format(event))
    uuid = event['campaign_uuid']
    type_name = event['type']

    campaign = fetch_campaign(campaign_path(uuid))
    for type_key in campaign['types']:
        if campaign['types'][type_key]['type'] == type_name:
            typee = campaign['types'][type_key]

    type_id = typee['type'].replace(' ', '_')
    if 'element_type' in typee:
        element_type = typee['element_type']
    else:
        element_type = None

    elements = []
    if element_type == 'Point':
        elements.append('node')
    elif element_type == 'Polygon':
        elements.append('way')
    elif element_type == 'Line':
        elements.append('way')
    else:
        elements.append('way')
        elements.append('node')

    query = build_query(uuid, type_id, elements)
    post_request(query, type_id)
    save_to_s3(
        path=build_path(uuid, type_id),
        type_id=type_id)
