import json
from aws import S3Data


def download_overpass_file(uuid, type_id):
    key = build_raw_data_overpass_path(
        campaign_path=campaign_path(uuid),
        type_id=type_id)

    S3Data().download_file(
        key=key,
        type_id=type_id,
        destination='/tmp')


def build_raw_data_overpass_path(campaign_path, type_id):
    return '/'.join([
        '{campaign_path}',
        'overpass',
        '{type_id}.xml']).format(
            campaign_path=campaign_path,
            type_id=type_id)


def to_piechart(data):
    return {
        'labels': list(data.keys()),
        'datasets': [{
            'data': list(data.values()),
            'backgroundColor': ['#4286f4']
        }]
    }


def campaign_path(uuid):
    return '/'.join([
        'campaigns',
        '{uuid}']).format(
            uuid=uuid)


def fetch_campaign(campaign_path):
    return S3Data().fetch('{campaign_path}/campaign.json'.format(
        campaign_path=campaign_path))


def fetch_type(seeked_feature, functions):
    return list(dict(filter(lambda function:
        is_function_and_feature(
            function_name=function[1]['function'],
            feature=function[1]['feature'],
            seeked_feature=seeked_feature),
        functions.items())).values())[0]['type']


def is_function_and_feature(function_name, feature, seeked_feature):
    return \
        function_name == 'CountFeature' \
        and \
        feature == seeked_feature


def save_data(uuid, type_id, data):
    with open('/tmp/data.json', 'w') as file:
        json.dump(data, file)

    data_path = build_render_data_path(
        campaign_path=campaign_path(uuid),
        type_id=type_id)

    with open('/tmp/data.json', 'rb') as data:
        S3Data().upload_file(
            key=data_path,
            body=data)


def build_render_data_path(campaign_path, type_id):
    return '/'.join([
        '{campaign_path}',
        'render/{type_id}',
        'count_feature.json']).format(
            campaign_path=campaign_path,
            type_id=type_id)
