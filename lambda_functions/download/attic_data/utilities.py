import json
import calendar
import datetime
from dependencies import requests
from aws import S3Data
from parser import ElementParser


def build_path(uuid, feature):
    return '/'.join([
        'campaigns/{uuid}',
        'raw_data/attic',
        '{feature}.xml']).format(
            uuid=uuid,
            feature=feature)


def build_query(uuid, feature):
    elements_ids = serialize_overpass_data(uuid, feature)

    parameters = {
        'element_parameters': cast_element_ids_to_s(elements_ids),
        'print_mode': 'meta'
    }
    return format_query(parameters)


def build_diff_query(date):
    date_from = cast_date_to_timgm(date['from'])
    date_to = cast_date_to_timgm(date['to'])

    datetime_from = datetime.datetime.utcfromtimestamp(
            float(date_from) / 1000.)
    datetime_to = datetime.datetime.utcfromtimestamp(
            float(date_to) / 1000.)
    date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    diff_query = '[diff:"{date_from}", "{date_to}"];'.format(
            date_from=datetime_from.strftime(date_format),
            date_to=datetime_to.strftime(date_format)
    )
    return diff_query


def format_query(parameters):
    return (
        '('
        '{element_parameters}'
        ');'
        '(._;>;);'
        'out {print_mode};'
    ).format(**parameters)


def post_request(query, feature):
    data = requests.post(
        # url='http://overpass-api.de/api/interpreter',
        url='http://overpass.hotosm.org/api/interpreter',
        data={'data': query},
        headers={'User-Agent': 'HotOSM'},
        stream=True)

    f = open('/tmp/attic_{feature}.xml'.format(feature), 'w')
    for line in data.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            f.write(decoded_line)
    f.close()


def save_to_s3(path, feature):
    with open('/tmp/attic_{feature}.xml'.format(feature), 'rb') as data:
        S3Data().upload_file(
            key=path,
            body=data)


def serialize_overpass_data(uuid, feature):
    path = 'campaigns/{uuid}/raw_data/overpass/{feature}.xml'.format(
        uuid=uuid,
        feature=feature)

    S3Data().download_file(
        key=path,
        feature=feature)

    xml_file = open('/tmp/{feature}.xml'.format(feature=feature), 'r')
    parser = ElementParser()
    import xml.sax

    try:
        xml.sax.parse(xml_file, parser)
    except xml.sax.SAXParseException:
        print('FAIL')

    return parser.elements_ids


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


def cast_date_to_timgm(date):
    return calendar.timegm(datetime.datetime.strptime(
            date, '%Y-%m-%d').timetuple()) * 1000


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
