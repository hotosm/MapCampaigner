import os
import sys
sys.path.insert(0, "dependencies")
import json
from aws import S3Data
from utilities import (
    fetch_campaign,
    fetch_campaign_geometry,
    build_feature_completeness_path,
    build_count_feature_path,
    campaign_path,
    build_template_path,
    render_templates,
    create_feature_details_json
)
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    try:
        main(event, context)
    except Exception as e:
        S3Data().create(
            key=f'campaigns/{event["campaign_uuid"]}/failure.json',
            body=json.dumps({'function': 'render_feature', 'failure': str(e)}))


def main(event, context):
    logger.info('got event{}'.format(event))
    uuid = event['campaign_uuid']
    type_name = event['type']
    type_id = type_name.replace(' ', '_')

    campaign = fetch_campaign(campaign_path(uuid))
    geometry = fetch_campaign_geometry(campaign_path(uuid))
    # type_name = fetch_type(feature, campaign['selected_functions'])

    print(type_name)
    print(type_id)

    for type_key in campaign['types']:
        if campaign['types'][type_key]['type'] == type_name:
            typee = campaign['types'][type_key]
    print(typee)

    data = {}
    # feature completeness
    feature_completeness_data_path = build_feature_completeness_path(
        campaign_path=campaign_path(uuid),
        type_id=type_id)

    data['feature_completeness'] = S3Data().fetch(feature_completeness_data_path)

    data['uuid'] = uuid
    data['type_id'] = type_id

    template_path = build_template_path(
        campaign_path=campaign_path(uuid),
        type_id=type_id)
    # count feature
    count_feature_data_path = build_count_feature_path(
        campaign_path=campaign_path(uuid),
        type_id=type_id)

    data['count_feature'] = S3Data().fetch(count_feature_data_path)
    data['geometry'] = geometry
    data['url'] = '/'.join([
        "https://s3-us-west-2.amazonaws.com/{bucket}",
        "campaigns/{uuid}",
        "render/{type_id}"]).format(
            bucket=os.environ['S3_BUCKET'],
            uuid=uuid,
            type_id=type_id)

    render_templates(template_path, data)
