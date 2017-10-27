__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '16/05/17'

import json
import os
import threading
import requests
from utilities import absolute_path
import tempfile
import time
import yaml
from shapely import geometry as shapely_geometry
from shapely.ops import cascaded_union
from shapely.geometry.geo import mapping

from reporter.osm import fetch_osm, fetch_osm_with_post
from app_config import Config
from reporter.exceptions import (
    OverpassBadRequestException,
    OverpassDoesNotReturnData
)


def module_path(*args):
    """Get an absolute path for a file that is relative to the root.

    :param args: List of path elements.
    :type args: list

    :returns: An absolute path.
    :rtype: str
    """
    return os.path.join(absolute_path(), 'campaign_manager')


def temporary_folder():
    """Get an absolute path for temp folder which
    is relative to the root."""
    temporary_folder = os.path.join(
        tempfile.gettempdir(), 'campaign-data')
    try:
        os.mkdir(temporary_folder)
    except OSError as e:
        pass
    return temporary_folder


def get_osm_user():
    osm_user_path = os.path.join(
        module_path(), 'osm_user.txt')
    with open(osm_user_path) as f:
        content = f.readlines()
    users = [x.strip() for x in content]
    users.sort()
    return users


def get_types():
    """ Get all types in json

    :return: json of survey of type
    :rtype: dict
    """
    survey_folder = os.path.join(
        Config.campaigner_data_folder,
        'surveys'
    )
    surveys = {}
    if os.path.exists(survey_folder):
        for filename in os.listdir(survey_folder):
            if '.gitkeep' in filename:
                continue

            # check the json for each file
            survey_path = os.path.join(
                survey_folder,
                filename
            )
            survey = get_survey_json(survey_path)
            surveys[filename] = survey
    return surveys


running_thread = []


class FetchOsmThread(threading.Thread):
    threadID = 0

    def __init__(self, file_path, url_path, post_data=None):
        self.threadID = file_path
        self.file_path = file_path
        self.url_path = url_path
        self.post_data = post_data
        threading.Thread.__init__(self)

    # third step, implement the run(), which will be invoked
    # at the notation: thread.start()
    def run(self):
        if self.threadID not in running_thread:
            running_thread.append(self.threadID)
            if self.post_data:
                fetch_osm_with_post(
                        self.file_path,
                        self.url_path,
                        self.post_data)
            else:
                fetch_osm(self.file_path, self.url_path)
            running_thread.remove(self.threadID)


def load_osm_document_cached(
        file_path,
        url_path,
        post_data=None,
        returns_json=True):
    """Load an cached osm document, update the results if 15 minutes old.

    :type file_path: basestring
    :param file_path: The path on the filesystem

    :param url_path: Path of the file
    :type url_path: str

    :param post_data: Data for post request
    :type post_data: str

    :param returns_json: Returns as a dictionary from json file
    :type returns_json: bool

    :returns: Dictionary that contains json on the file,
    last_update, and updating status.
    :rtype: dict
    """
    elapsed_seconds = 0
    limit_seconds = 900  # 15 minutes
    file_time = time.time()
    updating_status = False
    if os.path.exists(file_path):
        current_time = time.time()  # in unix epoch
        file_time = os.path.getmtime(file_path)  # in unix epoch
        elapsed_seconds = current_time - file_time

    osm_data = {'elements': []}
    if elapsed_seconds > limit_seconds or not os.path.exists(file_path):
        if not os.path.exists(file_path):
            try:
                if post_data:
                    fetch_osm_with_post(
                            file_path,
                            url_path,
                            post_data,
                            returns_format='json' if returns_json else 'xml')
                else:
                    fetch_osm(file_path, url_path)
            except (OverpassBadRequestException, OverpassDoesNotReturnData):
                return osm_data, file_time, updating_status

        else:
            FetchOsmThread(file_path, url_path, post_data).start()
            updating_status = True

    file_handle = None
    if os.path.exists(file_path):
        file_handle = open(file_path, 'rb')

    if returns_json and file_handle:
        try:
            osm_data = json.loads(file_handle.read().decode('utf-8'))
        except ValueError:
            pass
    else:
        osm_data = file_handle

    return osm_data, file_time, updating_status


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


def multi_feature_to_polygon(geojson):
    """ Convert multi features to be multipolygon
    as single geometry.

    :param geojson: Geojson that
    :type geojson: dict

    :return: Nice geojson with multipolygon
    :rtype:dict
    """
    cascaded_geojson = None
    if len(geojson['features']) > 0:
        polygons = []
        for feature in geojson['features']:
            polygons.append(shapely_geometry.Polygon(
                feature['geometry']['coordinates'][0]
            ))
        cascaded_polygons = cascaded_union(polygons)
        cascaded_geojson = mapping(cascaded_polygons)

        coords_length = len(json.dumps(cascaded_geojson['coordinates']))

        if coords_length > 1000:
            # Simplify the polygons
            simplified_polygons = simplify_polygon(cascaded_polygons, 0.001)
            cascaded_geojson = mapping(simplified_polygons)

    geojson['features'] = [{
        "type": "Feature", "properties": {},
        "geometry": cascaded_geojson
    }]
    return geojson


def get_survey_json(survey_file):
    """ Return survey types of campaign in json
    :param survey_file: path of survey to be checked
    :type survey_file: str

    :return: json of survey of type
    :rtype: dict
    """
    surveys = {}
    if os.path.isfile(survey_file):
        surveys = yaml.load(open(survey_file, 'r'))
        if isinstance(surveys, str):
            raise yaml.YAMLError

        tags = {}
        if 'tags' in surveys:
            for tag in surveys['tags']:
                if isinstance(tag, str):
                    tags[tag] = []
                else:
                    tags.update(tag)
        surveys['tags'] = tags
    return surveys


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


def map_provider():
    """Return map provider, if mapbox api token provided then use mapbox map.
    """
    try:
        from secret import MAPBOX_TOKEN
        provider = 'https://api.mapbox.com/styles/v1/hot/' \
                   'cj7hdldfv4d2e2qp37cm09tl8/tiles/256/{z}/{x}/{y}?' \
                   'access_token=' + MAPBOX_TOKEN

    except ImportError:
        provider = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'

    return provider


def get_coordinate_from_ip():
    """Get coordinate information from ip address.
    """
    url = 'http://ipinfo.io/json'
    response = requests.get(url)
    data = response.json()
    return data['loc']
