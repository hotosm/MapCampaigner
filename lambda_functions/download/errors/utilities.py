import os
import json
import boto3
from dependencies import requests
from aws import S3Data


def get_error_ids(uuid, feature):
    data = download_feature_completeness_file(uuid, feature)
    return cast_element_ids_to_s(data['error_ids'])


def download_feature_completeness_file(uuid, feature):
    feature_completeness_data_path = build_feature_completeness_path(campaign_path(uuid), feature)
    print(feature_completeness_data_path)
    return S3Data().fetch(feature_completeness_data_path)


def cast_element_ids_to_s(hash_element_ids):
    """
    Cast a hash of element ids to a string of element ids.

    :param hash_element_ids: node/relation/way ids
    :type hash_element_ids: hash

    :returns: a string of node/relation/way ids
    :rtype: str
    """
    elements_to_s = str()
    for el in ['node', 'relation', 'way']:
        if len(hash_element_ids[el]) > 0:
            el_to_s = '{}(id:{});'.format(
                el,
                ','.join(str(element)
                         for element in hash_element_ids[el]))
            elements_to_s += el_to_s
    return elements_to_s


def build_feature_completeness_path(campaign_path, feature):
    return '/'.join([
        '{campaign_path}',
        'render',
        '{feature}',
        'feature_completeness.json']).format(
            campaign_path=campaign_path,
            feature=feature)


def campaign_path(uuid):
    return '/'.join([
        'campaigns',
        '{uuid}']).format(
            uuid=uuid)


def format_query(parameters):
    return (
        '('
        '{element_parameters}'
        ');'
        '(._;>;);'
        'out {print_mode};'
    ).format(**parameters)


def build_query(uuid, feature):
    error_ids = get_error_ids(uuid, feature);
    parameters = {
        'element_parameters': error_ids,
        'print_mode': 'meta'
    }

    return format_query(parameters)    



def post_request(query, feature):
    data = requests.post(
        url='http://exports-prod.hotosm.org:6080/api/interpreter',
        data={'data': query},
        headers={'User-Agent': 'HotOSM'},
        stream=True)

    f = open('/tmp/{}.xml'.format(feature), 'w')
    for line in data.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            f.write(decoded_line)
    f.close()


def save_to_s3(path, feature):
    with open('/tmp/{feature}.xml'.format(
        feature=feature), 'rb') as data:
        S3Data().upload_file(
            key=path,
            body=data)

def build_path(uuid, feature):
    return '/'.join([
        'campaigns/{uuid}',
        'render/{feature}/errors.osm'
        ]).format(
            uuid=uuid,
            feature=feature)