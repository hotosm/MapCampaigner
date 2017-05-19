import json
import hashlib
import os

from reporter import config
from reporter.utilities import (
    split_bbox,
)
from reporter.osm import (
    load_osm_document
)
from urllib.parse import quote
from reporter.queries import TAG_MAPPING, OVERPASS_QUERY_MAP


def get_osm_data(bbox, feature):
    """Get osm data.
    
    :param bbox: String describing a bbox e.g. '106.78674459457397,
        -6.141301491467023,106.80691480636597,-6.133834354201348'

    :param feature: The type of feature to extract:
        buildings, building-points, roads, potential-idp, boundary-[1,11]
    :type feature: str
    
    :returns: A dict from retrieved OSM dataset.
    :rtype: dict
    """
    server_url = 'http://overpass-api.de/api/interpreter?data='

    tag_name = feature
    overpass_verbosity = 'body'

    try:
        coordinates = split_bbox(bbox)
    except ValueError:
        error = "Invalid area"
        coordinates = split_bbox(config.BBOX)

    feature_type = TAG_MAPPING[tag_name]
    parameters = coordinates
    parameters['print_mode'] = overpass_verbosity
    query = OVERPASS_QUERY_MAP[feature_type].format(**parameters)

    # Query to returns json string
    query = '[out:json];' + query

    encoded_query = quote(query)
    url_path = '%s%s' % (server_url, encoded_query)

    safe_name = hashlib.md5(query.encode('utf-8')).hexdigest() + '.osm'
    file_path = os.path.join(config.CACHE_DIR, safe_name)
    osm_document = load_osm_document(file_path, url_path)

    osm_data = json.loads(osm_document.read())

    return osm_data
