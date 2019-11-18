__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '16/05/17'

import json
import os
import threading
import requests
from utilities import absolute_path
import sys
import tempfile
import time
import yaml
from shapely import geometry as shapely_geometry
from shapely.ops import cascaded_union
from shapely.geometry.geo import mapping
from functools import reduce

from reporter.osm import fetch_osm, fetch_osm_with_post
from app_config import Config
from reporter.exceptions import (
    OverpassBadRequestException,
    OverpassDoesNotReturnData
)
from campaign_manager.aws import S3Data
from campaign_manager.models.survey import Survey

from glob import glob
from datetime import datetime

import xml.etree.ElementTree as ET


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


def get_allowed_managers():
    content = S3Data().fetch('managers.txt').split("\n")
    managers = [x.strip() for x in content]
    managers.sort()
    return managers


def get_types():
    """ Get all types in json

    :return: json of survey of type
    :rtype: dict
    """
    surveys = {}
    path = os.path.join(
        os.path.dirname(__file__),
        '../campaign_manager/feature_templates',
        '*.yml'
    )
    files = glob(path)
    for file in files:
        filename = os.path.splitext(os.path.split(file)[-1])[0]
        surveys[filename] = get_survey_json(file)
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
    return Survey.find_by_name(survey_file).data


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
    if 'MAPBOX_TOKEN' in os.environ:
        provider = 'https://api.mapbox.com/styles/v1/hot/' \
                   'cj7hdldfv4d2e2qp37cm09tl8/tiles/256/{z}/{x}/{y}?' \
                   'access_token=' + os.environ['MAPBOX_TOKEN']

    else:
        provider = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'

    return provider


def get_coordinate_from_ip():
    """Get coordinate information from ip address.
    """
    url = 'http://ipinfo.io/json'
    response = requests.get(url)
    data = response.json()
    return data['loc']


def get_uuids_from_cache(folder_path):
    # Get all json files from folder.
    cache_data = glob(os.path.join(folder_path, '*.json'))

    # Remove file format.
    cache_uuids = [c.split('.json')[0] for c in cache_data]

    # Remove absolute path.
    cache_uuids = [c.split('/')[-1] for c in cache_uuids]

    return cache_uuids


def get_data_from_s3(uuid, modified):
    s3 = S3Data()

    # Make a request to get the campaign json and geojson.
    campaign_json = s3.fetch('campaigns/{0}/campaign.json'.format(uuid))
    geojson = s3.fetch('campaigns/{0}/campaign.geojson'.format(uuid))
    campaign_json['geojson'] = geojson
    campaign_json['modified'] = modified

    return campaign_json


def get_data(campaign, cache, folder_path):
    uuid = campaign['uuid']
    if uuid in cache:
        # Read information from campaign.
        uuid_path = os.path.join(folder_path, '{0}.json'.format(uuid))
        with open(uuid_path, 'r') as f:
            data = json.load(f)

        # Check if the campaign has not been modified.
        if (campaign['modified'] - data['modified']) == 0:
            return data

    data = get_data_from_s3(uuid, campaign['modified'])

    # Save result in the cache directory.
    file_path = os.path.join(folder_path, '{0}.json'.format(uuid))
    with open(file_path, 'w') as f:
        json.dump(data, f)

    return data


def get_contribs(url, ctype):
    req = '{0}/render/{1}/mapper_engagement.json'
    resp = requests.get(req.format(url, ctype))

    # We return nothing. At the end, we filter results.
    if resp.status_code != 200:
        return None

    users = resp.json()

    # Create a separate list of contribution per date per user.
    data = [[[u['name'], ctype, t[0], t[1]] for t
            in json.loads(u['timeline'])] for u in users]

    # Flatten list.
    data = [item for sublist in data for item in sublist]

    return data


def geojson_to_gpx(geojson):
    root = ET.Element(
            "gpx",
            attrib=dict(
                xmlns="http://www.topografix.com/GPX/1/1",
                version="1.1",
                creator="HOT MapCampaigner",
            ),
    )
    # Create GPX Metadata element
    metadata = ET.Element("metadata")
    link = ET.SubElement(
        metadata,
        "link",
        attrib={'href': "https://github.com/hotosm/mapcampaigner"},
    )
    ET.SubElement(link, "text").text = "HOT MapCampaigner"
    ET.SubElement(metadata, "time").text = datetime.today().isoformat()
    root.append(metadata)
    # Create trk element
    trk = ET.Element("trk")
    root.append(trk)

    trkseg = ET.SubElement(trk, "trkseg")
    for coord in geojson['geometry']['coordinates'][0]:
        coord_dict = dict(lon=str(coord[0]), lat=str(coord[1]))
        ET.SubElement(trkseg, "trkpt", attrib=coord_dict,)

        # Append wpt elements to end of doc
        wpt = ET.Element("wpt", attrib=coord_dict)
        root.append(wpt)

    return ET.tostring(root, encoding="utf8")

def get_all_attributes(osm_elements):
    """Takes in a list of OSM elements and returns a list
    of the most attributes added by mappers"""
    attrs = list(map(get_attributes, osm_elements))
    attrs = [tag for tags in attrs for tag in tags]
    all_attrs = list(set(attrs))
    return all_attrs

def get_attributes(osm_element):
    """Takes in one OSM element and returns the attributes
    added by the mapper."""
    attributes_found = []
    tags = [desc for desc in osm_element.descendants if desc != ' ']
    if tags:
        attr = [tag["k"] for tag in tags if tag and tag.has_attr("k")]
        if attr:
            attributes_found = attr
    return attributes_found

def parse_osm_element(element, element_type, all_attrs):
    # Retrieve attributes
    attributes_found = get_attributes(element)
    attributes_not_found = list(set(all_attrs) - set(attributes_found))
    if not attributes_not_found:
        status = "Complete"
    else:
        status = "Incomplete"
    data = {"node_id": f'{element_type}:{element["id"]}',
            "status": status,
            "edited_by": element["user"],
            "edited_date": element["timestamp"],
            "attributes_found": attributes_found,
            "attributes_not_found": attributes_not_found}
    return data
