import json
import hashlib
import os
import re

from urllib.parse import quote

from reporter import config
from reporter.exceptions import OverpassTimeoutException
from reporter.queries import TAG_MAPPING, OVERPASS_QUERY_MAP_POLYGON
from reporter.utilities import split_polygon
from campaign_manager.data_providers._abstract_data_provider import (
    AbstractDataProvider
)
from campaign_manager.utilities import (
    load_osm_document_cached
)


class OverpassProvider(AbstractDataProvider):
    """Provider from overpass"""

    def get_data(self, feature, polygon):
        """Get osm data.

        :param feature: The type of feature to extract:
            buildings, building-points, roads, potential-idp, boundary-[1,11]
        :type feature: str

        :param polygon: list of array describing polygon area e.g.
        '[[28.01513671875,-25.77516058680343],[28.855590820312504,-25.567220388070023],
        [29.168701171875004,-26.34265280938059]]
        :type polygon: list

        :raises: OverpassTimeoutException

        :returns: A dict from retrieved OSM dataset.
        :rtype: dict
        """
        server_url = 'http://overpass-api.de/api/interpreter?data='

        tag_name = feature
        overpass_verbosity = 'body'

        try:
            polygon_string = split_polygon(polygon)
        except ValueError:
            error = "Invalid area"
            polygon_string = config.POLYGON

        feature_type = TAG_MAPPING[tag_name]
        parameters = dict()
        parameters['print_mode'] = overpass_verbosity
        parameters['polygon'] = polygon_string
        query = OVERPASS_QUERY_MAP_POLYGON[feature_type].format(**parameters)

        # Query to returns json string
        query = '[out:json];' + query

        encoded_query = quote(query)
        url_path = '%s%s' % (server_url, encoded_query)
        safe_name = hashlib.md5(query.encode('utf-8')).hexdigest() + '.osm'
        file_path = os.path.join(config.CACHE_DIR, safe_name)
        osm_document = load_osm_document_cached(file_path, url_path)

        osm_data = json.loads(osm_document.read())

        regex = 'runtime error:'
        if 'remark' in osm_data:
            if re.search(regex, osm_data['remark']):
                raise OverpassTimeoutException

        return osm_data['elements']
