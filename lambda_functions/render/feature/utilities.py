import os
import json
import boto3
from dependencies import jinja2
from aws import S3Data


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
    return S3Data().fetch('{campaign_path}/campaign.json'.format(
        campaign_path=campaign_path))


def fetch_campaign_geometry(campaign_path):
    return S3Data().fetch('{campaign_path}/campaign.geojson'.format(
        campaign_path=campaign_path))


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
