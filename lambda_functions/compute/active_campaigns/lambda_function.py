import os
import boto3
import json
from datetime import datetime
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


def lambda_handler(event, context):
    for campaign in Campaign.active():
        compute_campaign(campaign)
