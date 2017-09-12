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
        'node["%(KEY)s"]'
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
        'node["%(KEY)s"~"%(VALUE)s"]'
        '(poly:"{polygon}");'
        'relation["%(KEY)s"~"%(VALUE)s"]'
        '(poly:"{polygon}");'
        ');'
        '(._;>;);'
        'out {print_mode};'
    )

    query_with_id = (
        '('
        '{element_parameters}'
        ');'
        '(._;>;);'
        'out {print_mode};'
    )

    def get_data(
            self,
            polygon,
            feature_key,
            overpass_verbosity='meta',
            feature_values=None,
            date_from=None,
            date_to=None,
            returns_json=True,
            need_attic_data=False):
        """Get osm data.

        :param polygon: list of array describing polygon area e.g.
        '[[28.01513671875,-25.77516058680343],[28.855590820312504,-25.567220388070023],
        [29.168701171875004,-26.34265280938059]]
        :type polygon: list

        :param feature_key: The type of feature to extract:
            buildings, building-points, roads, potential-idp, boundary-[1,11]
        :type feature_key: str

        :param overpass_verbosity: Output verbosity in Overpass.
            It can be body, skeleton, ids_only or meta.
        :type overpass_verbosity: str

        :param feature_values: The value of features as query
        :type feature_values: list

        :param date_from: First date for date range.
        :type date_from: str

        :param returns_json: Returns as an object from json
        :type returns_json: bool

        :param date_to: Second date for date range.
        :type date_to: str

        :param need_attic_data: Request need attic data
        :type need_attic_data: bool

        :raises: OverpassTimeoutException

        :returns: A dict from retrieved OSM dataset.
        :rtype: dict
        """
        default_server_url = 'http://exports-prod.hotosm.org:6080/api/' \
                             'interpreter'
        attic_data_server_url = 'http://overpass-api.de/api/interpreter'

        if need_attic_data:
            server_url = attic_data_server_url
        else:
            server_url = default_server_url

        query = self.parse_url_parameters(
                polygon=polygon,
                feature_key=feature_key,
                feature_values=feature_values,
                overpass_verbosity=overpass_verbosity,
                response_format='json' if returns_json else 'xml',
                date_from=date_from,
                date_to=date_to
        )

        safe_name = hashlib.md5(query.encode('utf-8')).hexdigest() + '.osm'
        file_path = os.path.join(config.CACHE_DIR, safe_name)
        osm_data, osm_doc_time, updating = load_osm_document_cached(
                file_path, server_url, query, returns_json)

        if returns_json:
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
        else:
            return {
                'file': osm_data,
                'last_update': datetime.datetime.fromtimestamp(
                        osm_doc_time).strftime(
                        '%Y-%m-%d %H:%M:%S'),
                'updating_status': updating
            }

    def parse_url_parameters(
            self,
            polygon=None,
            feature_key=None,
            feature_values=None,
            overpass_verbosity='meta',
            response_format='xml',
            date_from=None,
            date_to=None,
            element_ids=None
    ):
        """Parse Overpass query.

        :param polygon: list of array describing polygon area e.g.
        '[[28.01513671875,-25.77516058680343],[28.855590820312504,-25.567220388070023],
        [29.168701171875004,-26.34265280938059]]
        :type polygon: list

        :param feature_key: The type of feature to extract:
            buildings, building-points, roads, potential-idp, boundary-[1,11]
        :type feature_key: str

        :param feature_values: The value of features as query
        :type feature_values: list

        :param overpass_verbosity: Output verbosity in Overpass.
            It can be body, skeleton, ids_only or meta.
        :type overpass_verbosity: str

        :param response_format: Format response from overpass query
        :type response_format: str

        :param date_from: First date for date range.
        :type date_from: str

        :param date_to: Second date for date range.
        :type date_to: str

        :param element_ids: Ids of node,way,relation
        :type element_ids: Dict[str, list]
        """
        parameters = dict()

        if polygon:
            try:
                polygon_string = split_polygon(polygon)
            except ValueError:
                error = "Invalid area"
                print(error)
                polygon_string = config.POLYGON
            parameters['polygon'] = polygon_string

        if element_ids:
            query = self.query_with_id
            element_parameters = ''
            if len(element_ids['node']) > 0:
                node_parameter = 'node(id:{NODE_IDS});'
                node_parameter = node_parameter.format(
                    NODE_IDS=','.join(element_ids['node'])
                )
                element_parameters += node_parameter

            if len(element_ids['way']) > 0:
                way_parameter = 'way(id:{WAY_IDS});'
                way_parameter = way_parameter.format(
                    WAY_IDS=','.join(element_ids['way'])
                )
                element_parameters += way_parameter

            if len(element_ids['relation']) > 0:
                relation_parameter = 'relation(id:{REL_IDS});'
                relation_parameter = relation_parameter.format(
                    REL_IDS=','.join(element_ids['relation'])
                )
                element_parameters += relation_parameter
            parameters['element_parameters'] = element_parameters

        elif feature_values:
            query = self.query_with_value % {
                'KEY': feature_key,
                'VALUE': '|'.join(feature_values)
            }
        else:
            query = self.query % {
                'KEY': feature_key
            }

        parameters['print_mode'] = overpass_verbosity
        query = query.format(**parameters)

        if date_from and date_to:
            try:
                datetime_from = datetime.datetime.utcfromtimestamp(
                        float(date_from) / 1000.)
                datetime_to = datetime.datetime.utcfromtimestamp(
                        float(date_to) / 1000.)
                date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
                diff_query = '[diff:"{date_from}", "{date_to}"];'.format(
                        date_from=datetime_from.strftime(date_format),
                        date_to=datetime_to.strftime(date_format)
                )
                query = diff_query + query
            except ValueError as e:
                print(e)
                pass

        if response_format == 'json':
            query = '[out:json];' + query

        return query

    def get_attic_data(
        self,
        polygon,
        feature_key,
        overpass_verbosity='meta',
        feature_values=None,
        date_from=None,
        date_to=None):
        """Get osm data.

        :param polygon: list of array describing polygon area e.g.
        '[[28.01513671875,-25.77516058680343],[28.855590820312504,-25.567220388070023],
        [29.168701171875004,-26.34265280938059]]
        :type polygon: list

        :param feature_key: The type of feature to extract:
            buildings, building-points, roads, potential-idp, boundary-[1,11]
        :type feature_key: str

        :param overpass_verbosity: Output verbosity in Overpass.
            It can be body, skeleton, ids_only or meta.
        :type overpass_verbosity: str-

        :param feature_values: The value of features as query
        :type feature_values: list

        :param date_from: First date for date range.
        :type date_from: str

        :param date_to: Second date for date range.
        :type date_to: str

        :raises: OverpassTimeoutException

        :returns: A dict from retrieved OSM dataset.
        :rtype: dict
        """

        server_url = 'http://overpass-api.de/api/interpreter'

        query = self.parse_url_parameters(
                polygon=polygon,
                feature_key=feature_key,
                feature_values=feature_values,
                overpass_verbosity=overpass_verbosity,
                response_format='json'
        )

        safe_name = hashlib.md5(query.encode('utf-8')).hexdigest() + '.osm'
        file_path = os.path.join(config.CACHE_DIR, safe_name)
        osm_data = None

        if os.path.exists(file_path):
            file_handle = open(file_path, 'rb')
            try:
                osm_data = json.loads(file_handle.read().decode('utf-8'))
            except ValueError:
                pass

        if not osm_data:
            safe_name = hashlib.md5(query.encode('utf-8')).hexdigest() + '.osm'
            file_path = os.path.join(config.CACHE_DIR, safe_name)
            osm_data, osm_doc_time, updating = load_osm_document_cached(
                    file_path, server_url, query, True)

        if osm_data:
            element_ids = {
                'node': [],
                'way': [],
                'relation': []
            }
            for element in osm_data['elements']:
                try:
                    element_ids[element['type']].append(str(element['id']))
                except ValueError:
                    pass
            element_query = self.parse_url_parameters(
                date_from=date_from,
                date_to=date_to,
                element_ids=element_ids
            )
            safe_name = hashlib.md5(
                    element_query.encode('utf-8')).hexdigest() + '.osm'
            file_path = os.path.join(config.CACHE_DIR, safe_name)
            print('Query attic data')
            osm_data, osm_doc_time, updating = load_osm_document_cached(
                    file_path, server_url, element_query, False)

            return {
                'file': osm_data,
                'last_update': datetime.datetime.fromtimestamp(
                        osm_doc_time).strftime(
                        '%Y-%m-%d %H:%M:%S'),
                'updating_status': updating
            }

        return None
