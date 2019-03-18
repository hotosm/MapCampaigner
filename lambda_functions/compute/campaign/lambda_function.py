import boto3
import json
import os
from aws import S3Data


def invoke_download_features(payload):
    aws_lambda = boto3.client('lambda')
    function_name_with_env = '{env}_{function_name}'.format(
        env=os.environ['ENV'],
        function_name='download_features')
    aws_lambda.invoke(
        FunctionName=function_name_with_env,
        InvocationType='RequestResponse',
        Payload=payload)


def remove_data(uuid):
    raw_data_key = "campaigns/{uuid}/overpass".format(
        uuid=uuid)

    for file in S3Data().list(raw_data_key):
        file_key = "{raw_data_key}/{file}".format(
            raw_data_key=raw_data_key,
            file=file)
        S3Data().delete(file_key)

    render_key = "campaigns/{uuid}/render".format(
        uuid=uuid)

    for typee in S3Data().list(render_key):
        render_typee_key = "{render_key}/{typee}".format(
            render_key=render_key,
            typee=typee)
        for file in S3Data().list(render_typee_key):
            file_key = "{render_typee_key}/{file}".format(
                render_typee_key=render_typee_key,
                file=file)
            S3Data().delete(file_key)

    S3Data().delete(f'campaigns/{uuid}/failure.json')


def lambda_handler(event, context):
    try:
        main(event, context)
    except Exception as e:
        S3Data().create(
            key=f'campaigns/{event["campaign_uuid"]}/failure.json',
            body=json.dumps({'function': 'compute_campaign', 'failure': str(e)}))


def main(event, context):
    uuid = event['campaign_uuid']
    payload = json.dumps({'campaign_uuid': uuid})

    remove_data(uuid)
    invoke_download_features(payload)
