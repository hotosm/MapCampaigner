import os
import json
import boto3
from dependencies import requests
from aws import S3Data


def fetch_campaign(campaign_path):
    return S3Data().fetch('{campaign_path}/campaign.json'.format(
        campaign_path=campaign_path))


def get_error_ids(uuid, type_id, elements):
    data = download_feature_completeness_file(uuid, type_id)
    return cast_element_ids_to_s(data['error_ids'], elements)


def download_feature_completeness_file(uuid, type_id):
    feature_completeness_data_path = build_feature_completeness_path(
        campaign_path=campaign_path(uuid),
        type_id=type_id)
    return S3Data().fetch(feature_completeness_data_path)


def cast_element_ids_to_s(hash_element_ids, elements):
    """
    Cast a hash of element ids to a string of element ids.

    :param hash_element_ids: node/relation/way ids
    :type hash_element_ids: hash

    :param elements: OSM element to search
    :type elements: array

    :returns: a string of node/relation/way ids
    :rtype: str
    """
    elements_to_s = str()
    for el in elements:
        if len(hash_element_ids[el]) > 0:
            el_to_s = '{}(id:{});'.format(
                el,
                ','.join(str(element)
                         for element in hash_element_ids[el]))
            elements_to_s += el_to_s
    return elements_to_s


def build_feature_completeness_path(campaign_path, type_id):
    return '/'.join([
        '{campaign_path}',
        'render',
        '{type_id}',
        'feature_completeness.json']).format(
            campaign_path=campaign_path,
            type_id=type_id)


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


def build_query(uuid, type_id, elements):
    error_ids = get_error_ids(uuid, type_id, elements)
    parameters = {
        'element_parameters': error_ids,
        'print_mode': 'meta'
    }

    return format_query(parameters)


def post_request(query, type_id):
    data = requests.post(
        url='http://overpass.hotosm.org/api/interpreter',
        data={'data': query},
        headers={'User-Agent': 'HotOSM'},
        stream=True)

    f = open('/tmp/{}.xml'.format(type_id), 'w')
    for line in data.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            f.write(decoded_line)
    f.close()


def save_to_s3(path, type_id):
    with open('/tmp/{type_id}.xml'.format(
        type_id=type_id), 'rb') as data:
        S3Data().upload_file(
            key=path,
            body=data)


def build_path(uuid, type_id):
    return '/'.join([
        'campaigns/{uuid}',
        'render/{type_id}/{uuid}_{type_id}_errors.osm'
        ]).format(
            uuid=uuid,
            type_id=type_id)
