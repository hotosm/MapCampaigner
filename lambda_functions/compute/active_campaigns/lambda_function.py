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

    files = s3.list_objects_v2(Bucket=bucket,
        Prefix=folder_path,
        Delimiter='/'
    )

    mbtiles_folder = 'campaigns/{0}/mbtiles/'.format(uuid)
    filter_folder = [f['Prefix'] for f in files['CommonPrefixes']
        if f['Prefix'] == mbtiles_folder]

    # No need to merge since there are no mbtiles folder.
    # TODO: Run mbtiles generation here (?).
    if len(filter_folder) == 0:
        return False

    # No campaign.mbtiles run merge command.
    mbtiles_file = 'campaigns/{0}/campaign.mbtiles'.format(uuid)
    filter_file = [f for f in files['Contents'] if f['Key'] == mbtiles_file]
    if len(filter_file) == 0:
        return True

    return False


def lambda_handler(event, context):
    aws_lambda = boto3.client('lambda')
    merge_func_name = '{0}_process_merge_mbtiles'.format(os.environ['ENV'])
    pdf_func_name = '{0}_process_make_pdf_grid'.format(os.environ['ENV'])

    for campaign in Campaign.active():
        compute_campaign(campaign)
        if needs_merge(campaign) is True:
            aws_lambda.invoke(
                FunctionName=merge_func_name,
                InvocationType='Event',
                Payload=json.dumps({'uuid': campaign})
            )

            aws_lambda.invoke(
                FunctionName=pdf_func_name,
                InvocationType='Event',
                Payload=json.dumps({'campaign_uuid': campaign})
            )
