import os
import json
import boto3
import logging
import gzip
from dependencies import jinja2
from aws import S3Data
from io import BytesIO


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def build_feature_completeness_path(campaign_path, type_id):
    return '/'.join([
        '{render_data_path}',
        'feature_completeness.json']).format(
            render_data_path=build_render_data_path(
                campaign_path=campaign_path,
                type_id=type_id))


def build_count_feature_path(campaign_path, type_id):
    return '/'.join([
        '{render_data_path}',
        'count_feature.json']).format(
            render_data_path=build_render_data_path(
                campaign_path=campaign_path,
                type_id=type_id))


def build_render_data_path(campaign_path, type_id):
    return '/'.join([
        '{campaign_path}',
        'render/{type_id}']).format(
            campaign_path=campaign_path,
            type_id=type_id)


def fetch_type(seeked_feature, functions):
    return list(dict(filter(lambda function:
        is_function_and_feature(
            function_name=function[1]['function'],
            feature=function[1]['feature'],
            seeked_feature=seeked_feature),
        functions.items())).values())[0]['type']


def is_function_and_feature(function_name, feature, seeked_feature):
    return \
        function_name == 'FeatureAttributeCompleteness' \
        and \
        feature == seeked_feature


def fetch_campaign(campaign_path):
    print("> Calling fetch_campaign")
    return S3Data().fetch('{campaign_path}/campaign.json'.format(
        campaign_path=campaign_path))


def fetch_campaign_geometry(campaign_path):
    print("> Calling fetch_campaign_geometry")
    return S3Data().fetch('{campaign_path}/campaign.geojson'.format(
        campaign_path=campaign_path))


def fetch_feature_geojson(feature_path):
    output_path = f'{feature_path}/geojson_1.json'
    print(f"output_path: {output_path}")
    # result = S3Data().fetch(output_path)
    print(f"bucket: {S3Data().bucket}")
    obj = S3Data().s3.get_object(
                Bucket=S3Data().bucket,
                Key=output_path)
    print("A")
    return obj['Body'].read()


def build_template_path(campaign_path, type_id):
    return '/'.join([
        '{campaign_path}',
        'render',
        '{type_id}']).format(
            campaign_path=campaign_path,
            type_id=type_id)


def render_templates(template_path, data):
    TEMPLATES = [
        'content',
        'map',
        'errors'
    ]

    for template in TEMPLATES:
        save_to_s3(
            path='{template_path}/{template}.html'.format(
                template_path=template_path,
                template=template),
            data=render_jinja_html(template, **data))


def render_jinja_html(template, **context):
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader('templates/')
    ).get_template(template + '.html').render(context)


def save_to_s3(path, data):
    S3Data().create(path, data)


def campaign_path(uuid):
    return '/'.join([
        'campaigns',
        '{uuid}']).format(
            uuid=uuid)


def build_processed_data_path(campaign_path, feature):
    return '/'.join([
        '{campaign_path}',
        'processed_data/{feature}',
        'feature_attribute_completeness',
        'data.json']).format(
            campaign_path=campaign_path,
            feature=feature)


def create_feature_details_json(feature_path, feature_type):
    print(f"feature_path: {feature_path}")
    try:
        list_geojson_files = S3Data().list(f"{feature_path}/geojson_")
        print(f"list_geojson_files: {list_geojson_files}")
    except Exception as d:
        print(d)
    #num_geojson_files = len(list_geojson_files)
    raw_data = fetch_feature_geojson(feature_path)
    print(f"raw_data: {raw_data}")
    print("B")
    zip_file = BytesIO(raw_data)
    print(f"zip_file: {zip_file}")
    print("C")
    try:
        unzip_file = gzip.GzipFile(fileobj=zip_file)
        print(f"unzip_file: {unzip_file}")
    except Exception as e:
        print(e)
    print("D")
    try:
        unzip_file = unzip_file.read()
        print(f"unzip_file2: {unzip_file}")
    except Exception as f:
        print(f)
    print("E")
    try:
        json_data = json.loads(unzip_file)
        print(f"json_data: {json_data}")
    except Exception as g:
        print(g)
    print("F")
    features_data = json_data["features"]
    print(f"features_data: {features_data}")
    for data in features_data:
        data["feature_type"] = feature_type
    print(f"features_data2: {features_data}")
    data = json.dumps(features_data)
    print(f"data: {data}")
    save_to = f'{feature_path}/feature.json'
    print(f"save_to: {save_to}")
    save_to_s3(save_to, data)
