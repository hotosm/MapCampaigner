import sys
sys.path.insert(0, 'dependencies')
import boto3
import json
import geojson as gj
import logging
import shapely.geometry as sp
import math
import os
import shutil
import zlib

from botocore.exceptions import ClientError
from os.path import join
from uuid import uuid4
from landez import MBTilesBuilder

# Maximum resolution of OSM
MAXRESOLUTION = 156543.0339

# X/Y axis offset
AXIS_OFFSET = MAXRESOLUTION * 256 / 2

# Where to save and read files.
PATH='/tmp/'

logging.basicConfig(level=logging.INFO)


def get_campaign(client):
    # Fetch geojson from s3.
    file_path = join('campaigns', client['uuid'], 'campaign.geojson')
    try:
        obj = client['obj'].get_object(Bucket=client['bucket'], Key=file_path)
    except ClientError as e:
        raise ValueError(e.response["Error"]["Message"])

    # decompress.
    result = obj['Body'].read()
    data = json.loads(result.decode('utf-8'))

    return data


def degrees_to_meters(lon, lat):
    x = lon * AXIS_OFFSET / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180)
    y = y * AXIS_OFFSET / 180

    return x, y


def meters_to_degrees(x, y):
    lon = x * 180 / AXIS_OFFSET
    # thanks magichim @ github for the correction
    lat = math.atan(math.exp(y * math.pi / AXIS_OFFSET)) * 360 / math.pi - 90

    return lon, lat


def create_task_feature(step, x, y):
    xmin = x * step - AXIS_OFFSET
    ymin = y * step - AXIS_OFFSET
    xmax = (x + 1) * step - AXIS_OFFSET
    ymax = (y + 1) * step - AXIS_OFFSET

    minlnglat = meters_to_degrees(xmin, ymin)
    maxlnglat = meters_to_degrees(xmax, ymax)

    bbox = [minlnglat[0], minlnglat[1], maxlnglat[0], maxlnglat[1]]

    return bbox


def create_grid(bbox, zoom):
    xmin, ymin, xmax, ymax = math.ceil(bbox[0]), math.ceil(
        bbox[1]), math.floor(bbox[2]), math.floor(bbox[3])

    step = AXIS_OFFSET / (math.pow(2, (zoom - 1)))

    xminstep = int(math.floor((xmin + AXIS_OFFSET) / step))
    xmaxstep = int(math.ceil((xmax + AXIS_OFFSET) / step))
    yminstep = int(math.floor((ymin + AXIS_OFFSET) / step))
    ymaxstep = int(math.ceil((ymax + AXIS_OFFSET) / step))
    task_features = []

    for x in range(xminstep, xmaxstep):
        for y in range(yminstep, ymaxstep):
            # print(x, ((2**zoom-1) - y) , zoom)
            task_feature = create_task_feature(step, x, y)
            task_features.append(task_feature)
    return task_features


def make_grid(bbox, zoom):
    minxy = degrees_to_meters(bbox[0], bbox[1])
    maxxy = degrees_to_meters(bbox[2], bbox[3])

    bbox = [minxy[0], minxy[1], maxxy[0], maxxy[1]]
    grid = create_grid(bbox, zoom)

    return grid


def get_bounds(poly):
    polygon = sp.Polygon(poly['geometry']['coordinates'][0])
    bounds = polygon.bounds

    return bounds


def create_grid_feature(box):
    poly = sp.box(*box)
    list_polygon = list(poly.exterior.coords)

    # Create geojson.
    feature = gj.Feature(
        geometry=gj.Polygon([list_polygon]),
        properties={"id": uuid4().hex}
    )

    return feature


def generate_mbtiles(grid, mbtiles_path, zoom_levels):
    mb = MBTilesBuilder(
        cache=False,
        tiles_headers={'User-Agent': 'github.com/hotosm/osm-export-tool'},
        filepath=mbtiles_path
    )

    for item in grid:
        mb.add_coverage(bbox=item, zoomlevels=zoom_levels)

    mb.run()


def create_folder(folder_path):
    if os.path.isdir(folder_path):
        logging.info('Deleting folder {0}'.format(folder_path))
        shutil.rmtree(folder_path)

    logging.info('Creating folder {0}'.format(folder_path))
    os.mkdir(folder_path)


def save_to_s3(client, uuid):
    logging.info('Uploading files to s3')
    # List elements.
    files = os.listdir(join(PATH, uuid))
    for f in files:
        key = join('campaigns', uuid, 'mbtiles', f)
        with open(join(PATH, uuid, f), "rb") as data:
            client['obj'].upload_fileobj(
                Fileobj=data,
                Bucket=client['bucket'],
                Key=key,
                ExtraArgs={'ACL': 'public-read'}
            )
        logging.info('Uploaded file to {0}'.format(key))


def lambda_handler(event, context):
    try:
        main(event)
    except Exception as e:
        error_dict = {'function': 'process_make_mbtiles', 'failure': str(e)}
        S3Data().create(
            key=f'campaigns/{event["campaign_uuid"]}/failure.json',
            body=json.dumps(error_dict))


def main(event):
    # Get data.
    uuid = event['uuid']
    zoom_levels = event['zoom_levels']
    grid_zoom_level = event['grid_zoom_level']

    client = {
        'obj': boto3.client("s3"),
        'bucket': os.environ['S3_BUCKET'],
        'uuid': uuid
    }

    logging.info('Fetching file: {0}'.format(client['uuid']))
    campaign_geojson = get_campaign(client)

    folder_path = join(PATH, uuid)
    create_folder(folder_path)

    features = []
    campaign_aois = campaign_geojson['features']

    logging.info('Campaign has {0} geometries'.format(len(campaign_aois)))
    for poly in campaign_aois:
        # Generate hex aoi for campaign and add it to features.
        aoi_hash = uuid4().hex
        poly['properties']['uuid'] = aoi_hash
        features.append(poly)

        bounds = get_bounds(poly)

        grid = make_grid(bounds, grid_zoom_level)

        logging.info('Found {0} boxes...Generating tiles'.format(len(grid)))

        for f in grid:
            features.append(create_grid_feature(f))

        mbtiles_path = join(folder_path, '{0}.mbtiles'.format(aoi_hash))
        generate_mbtiles(grid, mbtiles_path, zoom_levels)

    # Save new geojson.
    logging.info('Saving hashes to tiles.geojson')
    feature_collection = gj.FeatureCollection(features)
    geojson_outfile = join(folder_path, 'tiles.geojson')
    with open(geojson_outfile, 'w') as f:
        gj.dump(feature_collection, f)

    save_to_s3(client, uuid)
