import boto3
import json
import os


def invoke_download_features(payload):
    aws_lambda = boto3.client('lambda')
    function_name_with_env = '{env}_{function_name}'.format(
        env=os.environ['ENV'],
        function_name='download_features')
    aws_lambda.invoke(
        FunctionName=function_name_with_env,
        InvocationType='RequestResponse',
        Payload=payload)


def lambda_handler(event, context):
    uuid = event['campaign_uuid']
    payload = json.dumps({'campaign_uuid': uuid})
    
    invoke_download_features(payload)
