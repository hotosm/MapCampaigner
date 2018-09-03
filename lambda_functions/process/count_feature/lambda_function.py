import sys
sys.path.insert(0, "dependencies")
import logging
import xml.sax
from utilities import (
    fetch_campaign,
    campaign_path,
    fetch_type,
    to_piechart,
    download_overpass_file,
    save_data
)
from parser import CountFeatureParser


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info('got event{}'.format(event))
    uuid = event['campaign_uuid']
    feature = event['feature']
    
    feature_key = feature.split('=')[0]
    
    campaign = fetch_campaign(
        campaign_path=campaign_path(uuid))

    download_overpass_file(uuid, feature)
    xml_file = open('/tmp/{feature}.xml'.format(feature=feature), 'r')

    parser = CountFeatureParser(feature)

    try:
        xml.sax.parse(xml_file, parser)
    except xml.sax.SAXParseException:
        print('FAIL')

    type_name = fetch_type(feature, campaign['selected_functions'])
    type_id = type_name.replace(' ', '_')

    output = {
        'type_id': type_id,
        'type_name': type_name,    
        'piechart': to_piechart(parser.count)
    }

    save_data(uuid, type_id, output)
