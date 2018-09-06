import os
import boto3
import json
from dependencies.shapely import geometry
from aws import S3Data


def invoke_download_overpass_data(payload):
    aws_lambda = boto3.client('lambda')

    function_name_with_env = '{env}_download_overpass_data'.format(
        env=os.environ['ENV'])

    aws_lambda.invoke(
        FunctionName=function_name_with_env,
        InvocationType='Event',
        Payload=payload)


def get_unique_features(functions):
    features = []
    for function in functions:
        features.append(functions[function]['feature'])
    return set(features)


def parse_json_string(json_string):
    """Parse json string to object, if it fails then return none

    :param json_string: json in string format
    :type json_string: str

    :return: object or none
    :rtype: dict/None
    """
    json_object = None

    if not isinstance(json_string, str):
        return json_string

    try:
        json_object = json.loads(json_string)
    except (ValueError, TypeError):
        pass
    return json_object
