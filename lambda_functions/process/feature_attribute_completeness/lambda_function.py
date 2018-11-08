import sys
sys.path.insert(0, "dependencies")
import json
import logging
import xml.sax
from utilities import (
    campaign_path,
    fetch_campaign,
    fetch_type,
    fetch_required_tags,
    build_render_data_path,
    invoke_render_feature,
    invoke_download_errors,
    compute_completeness_pct,
    save_data,
    download_overpass_file,
)
from parser import FeatureCompletenessParser
from aws import S3Data


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info('got event{}'.format(event))
    uuid = event['campaign_uuid']
    feature = event['feature']
    
    campaign = fetch_campaign(campaign_path(uuid))
    required_tags = fetch_required_tags(feature, campaign['selected_functions'])
    
    type_name = fetch_type(feature, campaign['selected_functions'])
    type_id = type_name.replace(' ', '_')

    render_data_path = build_render_data_path(
        campaign_path=campaign_path(uuid),
        type_id=type_id)


    download_overpass_file(uuid, feature)


    xml_file = open('/tmp/{feature}.xml'.format(feature=feature), 'r')
    parser = FeatureCompletenessParser(required_tags, render_data_path)
    
    try:
        xml.sax.parse(xml_file, parser)
    except xml.sax.SAXParseException:
        print('FAIL')


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
    invoke_download_errors(uuid, feature)
    invoke_render_feature(uuid, feature)
