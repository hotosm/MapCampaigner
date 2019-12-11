import os
import boto3
import json
from campaign import Campaign


def compute_campaign(campaign_uuid):
    aws_lambda = boto3.client('lambda')
    payload = json.dumps({'campaign_uuid': campaign_uuid})
    function_name_with_env = '{env}_compute_campaign'.format(
        env=os.environ['ENV'])
    aws_lambda.invoke(
        FunctionName=function_name_with_env,
        InvocationType='Event',
        Payload=payload)


def needs_merge(uuid):
    # List all folders within the campaign one.
    s3 = boto3.client('s3')
    bucket = os.environ['S3_BUCKET']
    folder_path = 'campaigns/{0}/'.format(uuid)

    # Verify that mbtiles folder exists.
    mbtiles_folder = 'campaigns/{0}/mbtiles/'.format(uuid)
    mbtiles_files = s3.list_objects_v2(Bucket=bucket,
        Prefix=mbtiles_folder,
    )
    key_count = mbtiles_files['KeyCount']

    if key_count == 0:
        return False

    # Verify that all mbtiles tasks are completed.
    campaign_geojson = 'campaigns/{0}/campaign.geojson'.format(uuid)
    obj = s3.get_object(Bucket=bucket, Key=campaign_geojson)
    campaign_geojson = json.loads(obj['Body'].read())

    if key_count != len(campaign_geojson['features']) + 1:
        return False

    # No campaign.mbtiles run merge command.
    mbtiles_file_merged = 'campaigns/{0}/campaign.mbtiles'.format(uuid)
    mbtiles_fetch = s3.list_objects_v2(Bucket=bucket,
        Prefix=mbtiles_file_merged,
    )

    if mbtiles_fetch['KeyCount'] == 1:
        return False

    return True


def lambda_handler(event, context):
    aws_lambda = boto3.client('lambda')
    merge_func_name = '{0}_process_merge_mbtiles'.format(os.environ['ENV'])

    for campaign in Campaign.active():
        compute_campaign(campaign)
        if needs_merge(campaign) is True:
            aws_lambda.invoke(
                FunctionName=merge_func_name,
                InvocationType='Event',
                Payload=json.dumps({'uuid': campaign})
            )
