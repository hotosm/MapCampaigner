import datetime
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
    query = (
        '('
        'way["%(KEY)s"]'
        '(poly:"{polygon}");'
        'relation["%(KEY)s"]'
        '(poly:"{polygon}");'
        ');'
        '(._;>;);'
        'out {print_mode};'
    )
    query_with_value = (
        '('
        'way["%(KEY)s"~"%(VALUE)s"]'
        '(poly:"{polygon}");'
        'relation["%(KEY)s"~"%(VALUE)s"]'
        '(poly:"{polygon}");'
        ');'
        '(._;>;);'
        'out {print_mode};'
    )

    def get_data(self, polygon, feature_key, feature_values=None):
        """Get osm data.

        :param polygon: list of array describing polygon area e.g.
        '[[28.01513671875,-25.77516058680343],[28.855590820312504,-25.567220388070023],
        [29.168701171875004,-26.34265280938059]]
        :type polygon: list

        :param feature_key: The type of feature to extract:
            buildings, building-points, roads, potential-idp, boundary-[1,11]
        :type feature_key: str

        :param feature_values: The value of features as query
        :type feature_values: list

        :raises: OverpassTimeoutException

        :returns: A dict from retrieved OSM dataset.
        :rtype: dict
        """
        server_url = 'http://overpass-api.de/api/interpreter?data='

        overpass_verbosity = 'body'

        try:
            polygon_string = split_polygon(polygon)
        except ValueError:
            error = "Invalid area"
            polygon_string = config.POLYGON

        parameters = dict()
        parameters['print_mode'] = overpass_verbosity
        parameters['polygon'] = polygon_string

        if feature_values:
            query = self.query_with_value % {
                'KEY': feature_key,
                'VALUE': '|'.join(feature_values)
            }
        else:
            query = self.query % {
                'KEY': feature_key
            }
        query = query.format(**parameters)

        # Query to returns json string
        query = '[out:json];' + query

        encoded_query = quote(query)
        url_path = '%s%s' % (server_url, encoded_query)
        safe_name = hashlib.md5(query.encode('utf-8')).hexdigest() + '.osm'
        file_path = os.path.join(config.CACHE_DIR, safe_name)
        osm_data, osm_doc_time, updating = load_osm_document_cached(
            file_path, url_path)

        regex = 'runtime error:'
        if 'remark' in osm_data:
            if re.search(regex, osm_data['remark']):
                raise OverpassTimeoutException

        return {
            'features': osm_data['elements'],
            'last_update': datetime.datetime.fromtimestamp(
                osm_doc_time).strftime(
                '%Y-%m-%d %H:%M:%S'),
            'updating_status': updating
        }
