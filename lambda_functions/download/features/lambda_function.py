import sys
sys.path.insert(0, "dependencies")
import json
from campaign import Campaign
from utilities import (
    get_unique_features,
    invoke_download_overpass_data
)


def lambda_handler(event, context):
    uuid = event['campaign_uuid']
    print(uuid)
    campaign = Campaign(uuid)
    # features = get_unique_features(
    #     functions=campaign._content_json['selected_functions'])

    for type_key in campaign.types:
        payload = json.dumps({
            'campaign_uuid': uuid,
            'type': campaign.types[type_key]['type']
        })
        invoke_download_overpass_data(payload)
    # for feature in features:
    #     payload = json.dumps({
    #         'campaign_uuid': uuid,
    #         'feature': feature
    #     })
    #     invoke_download_overpass_data(payload)
