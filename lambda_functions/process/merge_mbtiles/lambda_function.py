import sys
sys.path.insert(0, 'dependencies')
import boto3
import os
import shutil

from glob import glob
from os.path import join
from sqlite3 import connect

S3 = boto3.client('s3')
BUCKET = os.environ['S3_BUCKET']
CAMPAIGN_TILES = 'campaign.mbtiles'
PATH = '/tmp'


def list_mbtiles(uuid):
    mbtiles_folder = 'campaigns/{0}/mbtiles/'.format(uuid)
    mbtiles = S3.list_objects_v2(
        Bucket=BUCKET,
        Prefix=mbtiles_folder
    )
    mbtiles = [m['Key'] for m in mbtiles['Contents']
        if m['Key'].endswith('.mbtiles')]

    return mbtiles


def merge_tiles(folder_path, merge_file):
    mbtiles = glob('{0}/*.mbtiles'.format(folder_path))

    mbtile = mbtiles.pop(0)
    shutil.copy(mbtile, merge_file)

    dst_conn = connect(merge_file)
    dst_cursor = dst_conn.cursor()

    query = '''INSERT OR REPLACE INTO
        tiles(zoom_level, tile_column, tile_row, tile_data)
        VALUES (?,?,?,?);'''

    for mbtile in mbtiles:
        src_conn = connect(mbtile)
        src_cursor = src_conn.cursor()

        sql_text = 'SELECT * FROM tiles'
        src_cursor.execute(sql_text)

        row = src_cursor.fetchone()
        while row is not None:
            dst_cursor.execute(query, row)
            row = src_cursor.fetchone()
        dst_conn.commit()


def lambda_handler(event, context):
    try:
        main(event)
    except Exception as e:
        error_dict = {'function': 'process_merge_mbtiles', 'failure': str(e)}
        key = f'campaigns/{event["uuid"]}/failure.json'
        S3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=json.dumps(error_dict),
            ACL='public-read')


def main(event):
    uuid = event['uuid']

    folder_path = join(PATH, uuid)

    if os.path.isdir(folder_path):
        shutil.rmtree(folder_path)
    os.mkdir(folder_path)

    # Download all one by one.
    for mbtile in list_mbtiles(uuid):
        file_name = mbtile.split('/')[-1]
        S3.download_file(BUCKET,
            mbtile,
            join(folder_path, file_name)
        )
    # Merge using sqlite.
    merge_file = join(PATH, CAMPAIGN_TILES)
    merge_tiles(folder_path, merge_file)

    key = 'campaigns/{0}/{1}'.format(uuid, CAMPAIGN_TILES)
    with open(merge_file, "rb") as data:
        S3.upload_fileobj(
            Fileobj=data,
            Bucket=BUCKET,
            Key=key,
            ExtraArgs={'ACL': 'public-read'}
        )
