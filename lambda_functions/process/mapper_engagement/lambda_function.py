import sys
sys.path.insert(0, "dependencies")
import calendar
import datetime
import json
from utilities import (
    fetch_campaign,
    campaign_path,
    download_overpass_file,
    osm_object_contributions,
    save_data
)
from aws import S3Data


def lambda_handler(event, context):
    try:
        main(event, context)
    except Exception as e:
        S3Data().create(
            key=f'campaigns/{event["campaign_uuid"]}/failure.json',
            body=json.dumps({'function': 'process_mapper_engagement', 'failure': str(e)}))


def main(event, context):
    uuid = event['campaign_uuid']
    type_name = event['type']
    type_id = type_name.replace(' ', '_')

    campaign = fetch_campaign(campaign_path(uuid))
    for type_key in campaign['types']:
        if campaign['types'][type_key]['type'] == type_name:
            typee = campaign['types'][type_key]

    download_overpass_file(uuid, type_id)

    xml_file = open('/tmp/{type_id}.xml'.format(type_id=type_id), 'r')

    tag_name = typee['feature'].split('=')[0]
    start_date = calendar.timegm(datetime.datetime.strptime(
            campaign['start_date'], '%Y-%m-%d').timetuple()) * 1000
    end_date = calendar.timegm(datetime.datetime.strptime(
            campaign['end_date'], '%Y-%m-%d').timetuple()) * 1000

    sorted_user_list = osm_object_contributions(
        xml_file,
        tag_name,
        start_date,
        end_date)

    save_data(uuid, type_id, sorted_user_list)
