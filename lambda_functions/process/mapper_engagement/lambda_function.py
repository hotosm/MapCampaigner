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
    fetch_type,
    save_data
)
from aws import S3Data


def lambda_handler(event, context):
    uuid = event['campaign_uuid']
    feature = event['feature']


    campaign = fetch_campaign(campaign_path(uuid))
    download_overpass_file(uuid, feature)
    xml_file = open('/tmp/{feature}.xml'.format(feature=feature), 'r')
    feature_key = feature.split('=')[0]

    tag_name = feature_key
    start_date = calendar.timegm(datetime.datetime.strptime(
            campaign['start_date'], '%Y-%m-%d').timetuple()) * 1000
    end_date = calendar.timegm(datetime.datetime.strptime(
            campaign['end_date'], '%Y-%m-%d').timetuple()) * 1000

    sorted_user_list = osm_object_contributions(
        xml_file,
        tag_name,
        start_date,
        end_date)

    type_name = fetch_type(feature, campaign['selected_functions'])
    type_id = type_name.replace(' ', '_')

    save_data(uuid, type_id, sorted_user_list)
