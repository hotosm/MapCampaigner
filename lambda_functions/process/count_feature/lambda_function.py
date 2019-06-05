import sys
sys.path.insert(0, "dependencies")
import logging
import json
import xml.sax
from utilities import (
    fetch_campaign,
    campaign_path,
    to_piechart,
    download_overpass_file,
    save_data
)
from parser import CountFeatureParser
from aws import S3Data


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    try:
        main(event, context)
    except Exception as e:
        S3Data().create(
            key=f'campaigns/{event["campaign_uuid"]}/failure.json',
            body=json.dumps({'function': 'process_count_feature', 'failure': str(e)}))


def main(event, context):
    logger.info('got event{}'.format(event))
    uuid = event['campaign_uuid']
    type_name = event['type']
    type_id = type_name.replace(' ', '_')

    campaign = fetch_campaign(
        campaign_path=campaign_path(uuid))
    for type_key in campaign['types']:
        if campaign['types'][type_key]['type'] == type_name:
            typee = campaign['types'][type_key]

    download_overpass_file(uuid, type_id)
    xml_file = open('/tmp/{type_id}.xml'.format(type_id=type_id), 'r')

    parser = CountFeatureParser(typee['feature'])

    try:
        xml.sax.parse(xml_file, parser)
    except xml.sax.SAXParseException:
        print('FAIL')

    output = {
        'type_id': type_id,
        'type_name': type_name,
        'piechart': to_piechart(parser.count)
    }

    save_data(uuid, type_id, output)
