import os
import json
import boto3
from dependencies import requests
from aws import S3Data
import xml.etree.cElementTree as ET
from dependencies.shapely import geometry


def clean_aoi(campaign, type_id):
    """ Clean the Area of Interest: remove ways and nodes from the OSM file
    that are outside the campaign's area.

    :param campaign: the campaign
    :type campaign: Campaign object

    :param type_id: campaign's type
    :type type_id: string
    """
    campaign_polygons = campaign.get_polygons()

    file = open('/tmp/{}.xml'.format(type_id), 'r')

    outside_polygons = find_outside_polygons(file, campaign_polygons)
    rebuild_osm_file(file, type_id, outside_polygons)


def rebuild_osm_file(file, type_id, outside_polygons):
    """ Build a new OSM file without the outside nodes and ways.

    :param file: the original OSM file
    :type file: fd

    :param type_id: campaign's type
    :type type_id: string

    :param outside_polygons: nodes and ways outside the campaign's areas
    :type outside_polygons: dictionnary
    """

    # go back to the beginning of the original file
    file.seek(0)

    clean_file = open('/tmp/{}_clean.xml'.format(type_id), 'w')
    clean_file.write('<?xml version="1.0" encoding="UTF-8"?>')

    for event, elem in ET.iterparse(file, events=('start', 'end')):
        if elem.tag == 'osm' and event == 'start':
            version = elem.attrib['version']
            generator = elem.attrib['generator']
            clean_file.write(f'<osm version="{version}" generator="{generator}">')

        if elem.tag == 'osm' and event == 'end':
            clean_file.write('</osm>')

        if elem.tag == 'note' and event == 'start':
            clean_file.write(f'<note>{elem.text}</note>')

        if elem.tag == 'meta' and event == 'start':
            osm_base = elem.attrib['osm_base']
            clean_file.write(f'<meta osm_base="{osm_base}"/>')

        if elem.tag == 'node' and event == 'start':
            # write nodes
            if elem.attrib['id'] not in outside_polygons['nodes']:
                el = ET.tostring(elem)
                clean_file.write(el.decode("utf-8"))

        if elem.tag == 'way' and event == 'start':
            if elem.attrib['id'] not in outside_polygons['ways']:
                el = ET.tostring(elem)
                clean_file.write(el.decode("utf-8"))

    os.rename('/tmp/{}.xml'.format(type_id), '/tmp/{}_orig.xml'.format(type_id))
    os.rename('/tmp/{}_clean.xml'.format(type_id), '/tmp/{}.xml'.format(type_id))


def find_outside_polygons(file, campaign_polygons):
    """ Find polygons outside the campaign's area

    :param file: the OSM file
    :type file: fd

    :param campaign_polygons: campaign's areas as Shapely Polygons
    :type campaign_polygons: list of Shapely Polygon

    :return out_ids: ids of nodes and ways that are outside campaign's areas.
    :rtype: dictionary
    """

    nodes = {}
    ways = {}
    in_way = False
    out_ids = {
        'nodes': [],
        'ways': []
    }

    for event, elem in ET.iterparse(file, events=('start', 'end')):
        # start of a node element
        # store its id, lon and lat
        if elem.tag == 'node' and event == 'start':
            nodes[elem.attrib['id']] = {
                'id': elem.attrib['id'],
                'lon': elem.attrib['lon'],
                'lat': elem.attrib['lat']
            }

        # start of way element
        if elem.tag == 'way' and event == 'start':
            # create a new way
            ways[elem.attrib['id']] = []
            in_way = True
            way_id = elem.attrib['id']

        # nd element in a way element
        if elem.tag == 'nd' and in_way is True:
            # fetch the node
            node = nodes[elem.attrib['ref']]
            ways[way_id].append(node)

        # end of way element
        if elem.tag == 'way' and event == 'end':
            in_way = False

            # create a shapely polygon
            polygon = []
            for point in ways[way_id]:
                polygon.append((float(point['lon']), float(point['lat'])))
            polygon = geometry.Polygon(polygon)

            # is the polygon in one of the campaign's polygons?
            is_in = False
            for campaign_polygon in campaign_polygons:
                if campaign_polygon.contains(polygon):
                    is_in = True

            if not is_in:
                node_ids = list(map(lambda x: x['id'], ways[way_id]))
                for node_id in node_ids:
                    out_ids['nodes'].append(node_id)

                out_ids['ways'].append(way_id)
    return out_ids


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


def invoke_process_count_feature(uuid, type_name):
    payload = json.dumps({
        'campaign_uuid': uuid,
        'type': type_name
    })

    invoke_process_function(
        function_name='process_count_feature',
        payload=payload)


def invoke_process_make_vector_tiles(uuid, type_name):
    payload = json.dumps({
        'campaign_uuid': uuid,
        'type': type_name
    })

    invoke_process_function(
        function_name='process_make_vector_tiles',
        payload=payload)


def invoke_process_feature_completeness(uuid, type_name):
    payload = json.dumps({
        'campaign_uuid': uuid,
        'type': type_name
    })

    invoke_process_function(
        function_name='process_feature_attribute_completeness',
        payload=payload)


def invoke_process_mapper_engagement(uuid, type_name):
    payload = json.dumps({
        'campaign_uuid': uuid,
        'type': type_name
    })

    invoke_process_function(
        function_name='process_mapper_engagement',
        payload=payload)


def format_query(parameters):
    if parameters['value']:
        if parameters['element_type'] == 'Point':
            query = template_node_query_with_value()
        elif (parameters['element_type'] == 'Line' or
            parameters['element_type'] == 'Polygon'):
            query = template_way_query_with_value()
        else:
            query = template_query_with_value()
    else:
        if parameters['element_type'] == 'Point':
            query = template_node_query()
        elif (parameters['element_type'] == 'Line' or
            parameters['element_type'] == 'Polygon'):
            query = template_way_query()
        else:
            query = template_query()

    return query.format(**parameters)


def format_feature_values(feature_values):
    return '|'.join(feature_values)


def build_query(polygon, typee):
    key, values = split_feature_key_values(typee['feature'])
    if 'element_type' in typee:
        element_type = typee['element_type']
    else:
        element_type = None

    parameters = {
        'polygon': split_polygon(polygon),
        'print_mode': 'meta',
        'key': key,
        'value': format_feature_values(values),
        'element_type': element_type
    }
    return format_query(parameters)


def build_query_path(uuid, type_id):
    return '/'.join([
        'campaigns/{uuid}',
        'overpass/{type_id}.query'
        ]).format(
            uuid=uuid,
            type_id=type_id)


def build_path(uuid, type_id):
    return '/'.join([
        'campaigns/{uuid}',
        'overpass/{type_id}.xml'
        ]).format(
            uuid=uuid,
            type_id=type_id)


def template_way_query():
    return (
        '[out:xml];('
        'way["{key}"]'
        '(poly:"{polygon}");'
        ');'
        '(._;>;);'
        'out {print_mode};'
    )


def template_way_query_with_value():
    return (
        '[out:xml];('
        'way["{key}"~"{value}"]'
        '(poly:"{polygon}");'
        ');'
        '(._;>;);'
        'out {print_mode};'
    )


def template_node_query_with_value():
    return (
        '[out:xml];('
        'node["{key}"~"{value}"]'
        '(poly:"{polygon}");'
        ');'
        '(._;>;);'
        'out {print_mode};'
    )


def template_node_query():
    return (
        '[out:xml];('
        'node["{key}"]'
        '(poly:"{polygon}");'
        ');'
        '(._;>;);'
        'out {print_mode};'
    )


def template_query():
    return (
        '[out:xml];('
        'way["{key}"]'
        '(poly:"{polygon}");'
        'node["{key}"]'
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
        ');'
        '(._;>;);'
        'out {print_mode};'
    )


def post_request(query, type_id):
    data = requests.post(
        url='http://exports-prod.hotosm.org:6080/api/interpreter',
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
    with open('/tmp/{type_id}.xml'.format(type_id=type_id), 'rb') as data:
        S3Data().upload_file(
            key=path,
            body=data)


def save_query(path, query):
    S3Data().create(
        key=path,
        body=query)


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
