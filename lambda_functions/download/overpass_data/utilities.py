import os
import json
import boto3
from dependencies import requests
from aws import S3Data


def build_payload(uuid, feature, date):
    return json.dumps({
        'campaign_uuid': uuid,
        'feature': feature,
        'date': date
    })


def invoke_process_function(function_name, payload):
    aws_lambda = boto3.client('lambda')
    function_name_with_env = '{env}_{function_name}'.format(
        env=os.environ['ENV'],
        function_name=function_name)

    aws_lambda.invoke(
        FunctionName=function_name_with_env,
        InvocationType='Event',
        Payload=payload)


def invoke_process_count_feature(uuid, feature):
    payload = json.dumps({
        'campaign_uuid': uuid,
        'feature': feature    
    })

    invoke_process_function(
        function_name='process_count_feature',
        payload=payload)


def invoke_process_feature_completeness(uuid, feature):
    payload = json.dumps({
        'campaign_uuid': uuid,
        'feature': feature    
    })

    invoke_process_function(
        function_name='process_feature_attribute_completeness',
        payload=payload)


def invoke_process_mapper_engagement(uuid, feature):
    payload = json.dumps({
        'campaign_uuid': uuid,
        'feature': feature    
    })

    invoke_process_function(
        function_name='process_mapper_engagement',
        payload=payload)


def format_query(parameters):
    if parameters['value']:
        query = template_query_with_value()
    else:
        query = template_query()

    return query.format(**parameters)


def format_feature_values(feature_values):
    return '|'.join(feature_values)


def build_query(polygon, feature):
    key, values = split_feature_key_values(feature)
    parameters = {
        'polygon': split_polygon(polygon),
        'print_mode': 'meta',
        'key': key,
        'value': format_feature_values(values)
    }
    return format_query(parameters)


def build_path(uuid, feature):
    return '/'.join([
        'campaigns/{uuid}',
        'raw_data/overpass/{feature}.xml'
        ]).format(
            uuid=uuid,
            feature=feature)


def template_query():
    return (
        '[out:xml];('
        'way["{key}"]'
        '(poly:"{polygon}");'
        'node["{key}"]'
        '(poly:"{polygon}");'
        'relation["{key}"]'
        '(poly:"{polygon}");'
        ');'
        '(._;>;);'
        'out {print_mode};'
    )


def template_query_with_value():
    return (
        '[out:xml];('
        'way["{key}"~"{value}"]'
        '(poly:"{polygon}");'
        'node["{key}"~"{value}"]'
        '(poly:"{polygon}");'
        'relation["{key}"~"{value}"]'
        '(poly:"{polygon}");'
        ');'
        '(._;>;);'
        'out {print_mode};'
    )


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


def date_to_dict(start_date, end_date):
    return {
        'from': start_date,
        'to': end_date
    }


def split_feature_key_values(feature):
    if '=' not in feature:
        feature = '{}='.format(feature)
    key, values = feature.split('=')
    if len(values) == 0:
        values = []
    else:
        values = values.split(',')
    return key, values


def split_polygon(polygon):
    """Split polygon array to string.

    :param polygon: list of array describing polygon area e.g.
    '[[28.01513671875,-25.77516058680343],[28.855590820312504,-25.567220388070023],
    [29.168701171875004,-26.34265280938059]]
    :type polygon: list

    :returns: A string of polygon e.g. 50.7 7.1 50.7 7.12 50.71 7.11
    :rtype: str
    """

    if len(polygon) < 3:
        raise ValueError(
                'At least 3 lat/lon float value pairs must be provided')

    polygon_string = ''

    for poly in polygon:
        polygon_string += ' '.join(map(str, poly))
        polygon_string += ' '

    return polygon_string.strip()


def simplify_polygon(polygon, tolerance):
    """Simplify polygon geometry.

    :param polygon: polygon object to simplified
    :type polygon: Shapely polygon

    :param tolerance: tolerance of simplification
    :type tolerance: float
    """
    simplified_polygons = polygon.simplify(
        tolerance,
        preserve_topology=True
    )
    return simplified_polygons


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
