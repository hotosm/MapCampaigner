import sys
sys.path.insert(0, "dependencies")
import json
import logging
import xml.sax
from utilities import (
    campaign_path,
    fetch_campaign,
    build_render_data_path,
    invoke_render_feature,
    invoke_download_errors,
    compute_completeness_pct,
    save_data,
    download_overpass_file,
    fix_tags
)
from parser import FeatureCompletenessParser
from aws import S3Data


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    try:
        main(event, context)
    except Exception as e:
        S3Data().create(
            key=f'campaigns/{event["campaign_uuid"]}/failure.json',
            body=json.dumps({
                'function': 'process_feature_attribute_completeness',
                'failure': str(e)
                })
            )


def main(event, context):
    logger.info('got event{}'.format(event))
    uuid = event['campaign_uuid']
    type_name = event['type']
    type_id = type_name.replace(' ', '_')

    campaign = fetch_campaign(campaign_path(uuid))
    for type_key in campaign['types']:
        if campaign['types'][type_key]['type'] == type_name:
            typee = campaign['types'][type_key]

    logger.info(typee['tags'])
    required_tags = fix_tags(typee['tags'])
    logger.info(required_tags)

    render_data_path = build_render_data_path(
        campaign_path=campaign_path(uuid),
        type_id=type_id)

    download_overpass_file(uuid, type_id)

    if 'element_type' in typee:
        element_type = typee['element_type']
    else:
        element_type = None

    xml_file = open('/tmp/{type_id}.xml'.format(type_id=type_id), 'r')
    parser = FeatureCompletenessParser(
        required_tags,
        render_data_path,
        element_type
        )

    try:
        xml.sax.parse(xml_file, parser)
    except xml.sax.SAXParseException:
        print('FAIL')
        parser.endDocument()

    processed_data = {
        'type_id': type_id,
        'type_name': type_name,
        'percentage': compute_completeness_pct(
            features_collected=parser.features_collected,
            features_completed=parser.features_completed),
        'features_collected': parser.features_collected,
        'features_completed': parser.features_completed,
        'checked_attributes': list(required_tags.keys()),
        'geojson_files_count': parser.geojson_file_manager.count,
        'errors_files_count': parser.errors_file_manager.count,
        'error_ids': parser.error_ids
    }
    save_data(uuid, type_id, processed_data)
    invoke_download_errors(uuid, type_name)
    invoke_render_feature(uuid, type_name)
