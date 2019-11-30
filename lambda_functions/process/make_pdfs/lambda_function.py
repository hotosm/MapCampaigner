from io import BytesIO
import math
import os
import json
import sys
import boto3

sys.path.insert(0, 'dependencies')

from shapely.geometry import box, Polygon, MultiPolygon
from aws import S3Data
from landez import ImageExporter
from PIL import Image, ImageDraw, ImageFont
from pyproj import Transformer


MAXRESOLUTION = 156543.0339

AXIS_OFFSET = MAXRESOLUTION * 256 / 2


def degrees_to_meters(lon, lat):
    x = lon * AXIS_OFFSET / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180)
    y = y * AXIS_OFFSET / 180

    return x, y


def meters_to_degrees(x, y):
    lon = x * 180 / AXIS_OFFSET
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
    xmin = math.ceil(bbox[0])
    ymin = math.ceil(bbox[1])
    xmax = math.floor(bbox[2])
    ymax = math.floor(bbox[3])
    step = AXIS_OFFSET / (math.pow(2, (zoom - 1)))
    xminstep = int(math.floor((xmin + AXIS_OFFSET) / step))
    xmaxstep = int(math.ceil((xmax + AXIS_OFFSET) / step))
    yminstep = int(math.floor((ymin + AXIS_OFFSET) / step))
    ymaxstep = int(math.ceil((ymax + AXIS_OFFSET) / step))
    task_features = []

    for x in range(xminstep, xmaxstep):
        for y in range(yminstep, ymaxstep):
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
    polygon = Polygon(poly['geometry']['coordinates'][0])
    bounds = polygon.bounds
    return bounds


def scale_coords(img, bounds, coords):
    transformer = Transformer.from_crs(4326, 3857)
    coords_transformed = []
    transform_1 = transformer.transform(bounds[3], bounds[0])
    transform_2 = transformer.transform(bounds[1], bounds[2])
    y = transform_2[0] - transform_1[0]
    x = transform_1[1] - transform_2[1]
    x_scale = img.size[1] / x
    y_scale = img.size[0] / y
    for coord in coords:
        a = transformer.transform(coord[1], coord[0])
        c = [abs(abs(transform_1[0]) - abs(a[0])),
             abs(abs(transform_1[1]) - abs(a[1]))]
        c = [c[0] * x_scale, c[1] * y_scale]
        coords_transformed.append(tuple(c))
    return coords_transformed


def stitch_tiles(mbtiles, features, bounds):
    ie = ImageExporter(mbtiles_file=mbtiles)
    f = BytesIO()
    f.name = '/tmp/temp.png'
    ie.export_image(
        bbox=bounds,
        zoomlevel=16,
        imagepath=f
    )
    img = Image.open(f)
    for feature in features:
        draw = ImageDraw.Draw(img)
        coords = feature['geometry']['coordinates'][0]
        coords_transformed = scale_coords(img, bounds, coords)
        draw.line(coords_transformed, fill="#FF00FF", width=5)
    return img


def crop_pdf(img, bounds, feature, idx):
    coords = feature['geometry']['coordinates'][0]
    coords_transformed = scale_coords(img, bounds, coords)
    cropped = img.crop((coords_transformed[0][0], coords_transformed[1][1],
                        coords_transformed[2][0], coords_transformed[0][1]))
    resized = cropped.resize((770, 523), Image.ANTIALIAS)
    pdf = Image.new('RGB', (842, 595), (255, 255, 255))
    pdf.paste(resized, box=(36, 36), mask=resized.split()[3])
    draw = ImageDraw.Draw(pdf)
    draw.rectangle([36, 36, 52, 52], fill=(255, 255, 255, 128))
    draw.text((40, 40), f"{idx}", fill=(0, 0, 0))
    return pdf


def create_legend(img, bounds, grid):
    legend = Image.new('RGB', img.size, (255, 255, 255))
    legend.paste(img, mask=img.split()[3])
    for i, feature in enumerate(grid):
        draw = ImageDraw.Draw(legend)
        coords = feature['geometry']['coordinates'][0]
        coords_transformed = scale_coords(legend, bounds, coords)
        draw.line(coords_transformed, fill="#000", width=4)
        h = coords_transformed[2][0] - coords_transformed[0][0]
        w = coords_transformed[0][1] - coords_transformed[1][1]
        label_coord = (coords_transformed[2][0] - h / 2,
                       coords_transformed[0][1] - w / 2)
        draw.text(label_coord, f"{i}", fill=(0, 0, 0))
    return legend


def main(event, context):
    uuid = event['campaign_uuid']
    geojson = S3Data().fetch(f'campaigns/{uuid}/mbtiles/tiles.geojson')
    campaign = S3Data().fetch(f'campaigns/{uuid}/campaign.geojson')
    aois = geojson['features']
    for aoi in aois:
        aoi_id = aoi['properties']['id']
        bounds = get_bounds(aoi)
        grid = make_grid(bounds, 16)
        features = []
        for item in grid:
            poly = list(box(*item).exterior.coords)
            polygon = Polygon(poly)
            features.append(polygon)
        multi_poly = MultiPolygon(features)
        bounds = multi_poly.bounds
        mbtiles_key = f'campaigns/{uuid}/mbtiles/{aoi_id}.mbtiles'
        with open(f'/tmp/{aoi_id}.mbtiles', 'wb') as f:
            boto3.client('s3').download_fileobj(os.environ['S3_BUCKET'],
                                                mbtiles_key, f)
        img = stitch_tiles(f'/tmp/{aoi_id}.mbtiles', campaign['features'],
                           bounds)
        g = S3Data().fetch(f'campaigns/{uuid}/pdf/grid.geojson')
        grid_features = [cell for cell in g['features'] if
                         cell['properties']['id'] == aoi['properties']['id']]
        legend = create_legend(img, bounds, grid_features)
        legend_buffer = BytesIO()
        legend.save(legend_buffer, "PDF", resolution=100.0)
        legend_buffer.seek(0)
        legend_pdf_key = f'campaigns/{uuid}/pdf/{aoi_id}/legend.pdf'
        S3Data().create(legend_pdf_key, legend_buffer)
        for i, b in enumerate(grid_features):
            pdf = crop_pdf(img, bounds, b, i)
            pdf_buffer = BytesIO()
            pdf.save(pdf_buffer, "PDF", resolution=100.0)
            pdf_buffer.seek(0)
            pdf_key = f'campaigns/{uuid}/pdf/{aoi_id}/{i}.pdf'
            S3Data().create(pdf_key, pdf_buffer)


def lambda_handler(event, context):
    try:
        main(event, context)
    except Exception as e:
        S3Data().create(
            key=f'campaigns/{event["campaign_uuid"]}/failure.json',
            body=json.dumps({
                'function': 'process_make_pdfs',
                'failure': str(e)
                })
            )
