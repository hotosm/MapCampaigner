import sys
sys.path.insert(0, "dependencies")
import json
from campaign import Campaign
from utilities import invoke_download_overpass_data
from aws import S3Data


def lambda_handler(event, context):
    try:
        main(event, context)
    except Exception as e:
        S3Data().create(
            key=f'campaigns/{event["campaign_uuid"]}/failure.json',
            body=json.dumps({'function': 'download_features', 'failure': str(e)}))


def main(event, context):
    uuid = event['campaign_uuid']
    campaign = Campaign(uuid)

    for type_key in campaign.types:
        payload = json.dumps({
            'campaign_uuid': uuid,
            'type': campaign.types[type_key]['type']
        })
        invoke_download_overpass_data(payload)
