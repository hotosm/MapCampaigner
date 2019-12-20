import os
import http.client
import csv
import json
from flask_restful import Resource, Api, reqparse
from flask import request, send_file
import logging

from io import BytesIO, StringIO
import boto3
import json
from zipfile import ZipFile
import xml.etree.ElementTree as xee
from xml.etree.ElementTree import fromstring, ElementTree, XMLParser, tostring

from campaign_manager import campaign_manager
from campaign_manager.models.campaign import Campaign
from campaign_manager.insights_functions.mapper_engagement import \
    MapperEngagement
from campaign_manager.utilities import get_coordinate_from_ip, \
    get_uuids_from_cache, get_data, get_data_from_s3
from campaign_manager.aws import S3Data

from reporter import config

api = Api(campaign_manager)


class UserCampaigns(Resource):
    """Shows a list of all campaigns"""
    def get(self, osm_id):
        user = S3Data().fetch(f'user_campaigns/{osm_id}.json')
        if not user:
            return []
        campaigns = [
            get_data_from_s3(campaign["uuid"], "")
            for campaign in user['projects']
        ]
        return campaigns


class CampaignList(Resource):
    """Shows a list of all campaigns"""

    def get(self):
        campaign_uuids = S3Data().list('campaigns')

        folder_path = os.path.join(config.CACHE_DIR, 'campaigns')

        # Check that folder exists. If not, create it.
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)

        cached_uuids = get_uuids_from_cache(folder_path)

        # Get all campaign information from either s3 or cache directory.
        campaigns = [
            get_data(campaign, cached_uuids, folder_path)
            for campaign in campaign_uuids
            ]

        return campaigns


class CampaignNearestList(Resource):
    """Show a list of nearest campaigns"""
    def get_nearest_campaigns(self, coordinate, campaign_status, args):
        """Returns all nearest campaign.

        :param campaign_status: status of campaign, active or inactive
        :type campaign_status: str

        :param coordinate: coordinate of user e.g. -4.1412,1.412
        :type coordinate: str.
        """
        return Campaign.nearest_campaigns(coordinate, campaign_status, **args)

    def get(self, campaign_status):
        """Get all nearest campaigns.

        :param campaign_status: status of campaign, active or inactive
        :type campaign_status: str
        """
        args = request.args
        if 'lon' in args and 'lat' in args:
            lon = args['lon']
            lat = args['lat']
            coordinate = lat + ',' + lon
        else:
            coordinate = get_coordinate_from_ip()
        campaigns = self.get_nearest_campaigns(
            coordinate,
            campaign_status,
            args
        )
        campaigns_json = []

        for campaign in campaigns:
            campaigns_json.append(campaign.json())

        return campaigns_json


class CampaignNearestWithTagList(Resource):
    """Show a list of nearest campaigns with tag filter"""

    def get(self, coordinate, tag):
        """Get all nearest campaigns.

        :param coordinate: coordinate of user e.g. -4.1412,1.412
        :type coordinate: str

        :param tag: tag to filter
        :type tag: str
        """
        campaigns = Campaign.nearest_campaigns(coordinate, **{
            'tags': tag
        })
        campaigns_json = []

        for campaign in campaigns:
            campaigns_json.append(campaign.json())

        return campaigns_json


class CampaignTagList(Resource):
    """Shows a list of all campaigns with tag filter"""

    def get_campaigns(self, tag):
        """Returns campaign with tag.

        :param tag: tag to filter
        :type tag: str
        """
        return Campaign.all(**{
            'tags': tag
                })

    def get(self, tag):
        """Get all campaigns.

        :param tag: tag to filter
        :type tag: str
        """
        campaigns = self.get_campaigns(tag)
        campaigns_json = []

        for campaign in campaigns:
            campaigns_json.append(campaign.json())

        return campaigns_json


class CampaignTotal(Resource):
    """Show total of campaign and participants."""

    def get_campaigns(self):
        """Returns campaigns.
        """
        return Campaign.all(campaign_status='active')

    def get(self):
        """Get total of campaign and participants."""
        campaigns = self.get_campaigns()
        participants_total = 0
        for campaign in campaigns:
            if campaign.total_participants_count:
                participants_total += campaign.total_participants_count

        return {
            'campaign_total': len(campaigns),
            'participant_total': participants_total
        }


class CampaignContributors(Resource):
    """Show Campaign Contributors."""
    feature = None

    def get_campaign(self, uuid):
        """Return campaign."""
        return Campaign(uuid=uuid)

    def get(self, uuid, feature):
        """Get total contributors."""

        campaign = self.get_campaign(uuid)

        user = []

        mapper = MapperEngagement(
            campaign=campaign, feature=feature)
        mapper.run()
        data = mapper.get_function_data()

        for entry in data['user_list']:
            if entry['name'] not in user:
                user.append(entry['name'])

        contributors_total = len(user)

        return {'contributors_total': contributors_total}


class PDFBundle(Resource):
    """ download zipfile of project pdfs in single file """

    def get(self, uuid):
        s3_client = S3Data()
        s3 = s3_client.s3
        grid_file = s3.get_object(Bucket=s3_client.bucket,
                            Key=f"campaigns/{uuid}/pdf/grid.geojson")
        grid = json.loads(grid_file['Body'].read())
        ids = [cell['properties']['id'] for cell in grid['features']]
        bundle_buffer = BytesIO()
        with ZipFile(bundle_buffer, 'w') as zip_obj:
            for grid_id in ids:
                dir_path = f'campaigns/{uuid}/pdf/{grid_id}/'
                kwargs = {"Bucket": s3_client.bucket,
                          "Prefix": dir_path}
                resp = s3.list_objects_v2(**kwargs)
                try:
                    pdfs = [obj['Key'] for obj in resp['Contents']]
                except KeyError:
                    continue
                for pdf in pdfs:
                    pdf_file = s3.get_object(Bucket=s3_client.bucket,
                            Key=pdf)
                    file_buffer = BytesIO()
                    file_buffer.write(pdf_file['Body'].read())
                    file_buffer.seek(0)
                    pdf_filename = f"{'/'.join(pdf.split('/')[-2:])}"
                    zip_obj.writestr(pdf_filename, file_buffer.getvalue())
        bundle_buffer.seek(0)
        resp = send_file(bundle_buffer,
                    as_attachment=True,
                    attachment_filename=f'pdf_bundle.zip',
                    mimetype='application/zip')
        return resp


class PDFBundleById(Resource):
    """ Download zipfile bundle of PDFs by grid id """

    def get(self, uuid, grid_id):
        dir_path = f'campaigns/{uuid}/pdf/{grid_id}/'
        s3_client = S3Data()
        s3 = s3_client.s3
        kwargs = {"Bucket": s3_client.bucket,
                  "Prefix": dir_path}
        resp = s3.list_objects_v2(**kwargs)
        pdfs = [obj['Key'] for obj in resp['Contents']]
        bundle_buffer = BytesIO()
        with ZipFile(bundle_buffer, 'w') as zip_obj:
            for pdf in pdfs:
                pdf_file = s3.get_object(Bucket=s3_client.bucket,
                        Key=pdf)
                file_buffer = BytesIO()
                file_buffer.write(pdf_file['Body'].read())
                file_buffer.seek(0)
                pdf_filename = f"{pdf.split('/')[-1]}"
                zip_obj.writestr(pdf_filename, file_buffer.getvalue())
        bundle_buffer.seek(0)
        resp = send_file(bundle_buffer,
                    as_attachment=True,
                    attachment_filename=f'{grid_id}.zip',
                    mimetype='application/zip')
        return resp


class UserSearch(Resource):
    """ Proxy requests to whosthat """

    def get(self, name):
        """ get possible user profiles by name:str"""
        conn = http.client.HTTPConnection("whosthat.osmz.ru")
        conn.request("GET", f"/whosthat.php?action=names&q={name}")
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))


class AllFeatures(Resource):
    """ Merge feature jsons to one """

    def get(self, uuid):
        args = request.args
        username = args.get('username', None)
        campaign = S3Data().fetch(f'campaigns/{uuid}/campaign.json')

        features = [f['type'].replace(' ', '_') for _, f
            in campaign['types'].items()]

        all_features = []
        for feature in features:
            feature_json = S3Data().fetch(f'campaigns/{uuid}/{feature}.json')
            all_features += feature_json
        if username:
            user_features = [f for f in all_features
                            if f['last_edited_by'] == username]
            return user_features
        return all_features


class GetFeature(Resource):
    """ Merge feature jsons to one """

    def get(self, uuid, feature_name):
        feature_json = S3Data().fetch(f'campaigns/{uuid}/{feature_name}.json')
        return feature_json


def filter_json(json_data, filters):
    if not filters:
        return json_data
    for k,v in filters.items():
        json_data = [item for item in json_data if item[k] == v]
    return json_data


def filter_xml(xml_data, filters):
    if not filters:
        return xml_data
    doc = xee.fromstring(xml_data)
    for k,v in filters.items():
        for tag in doc.findall('node'):
            if tag.attrib[k] != v:
                doc.remove(tag)
        for tag in doc.findall('way'):
            if tag.attrib[k] != v:
                doc.remove(tag)
    return xee.tostring(doc)


def merge_xml(xml_files):
    node = None
    parser = XMLParser(encoding="utf-8")
    for xml_file in xml_files:
        tree = ElementTree(fromstring(xml_file))
        root = tree.getroot()
        if node is None:
            node = root
        else:          
            for child in root:
                if child.tag in ('way', 'node'):
                    node.append(child)
    return tostring(node)


class DownloadFeatures(Resource):
    """ download feature list """

    def post(self, uuid):
        parser = reqparse.RequestParser()
        parser.add_argument('fileFormat', type=str)
        parser.add_argument('username', type=str)
        parser.add_argument('filter', type=dict)
        args = parser.parse_args()
        file_format = args.get('fileFormat', None)
        username = args.get('username', None)
        filters = args.get('filter', {})
        campaign = S3Data().fetch(f'campaigns/{uuid}/campaign.json')
        features = [f['type'].replace(' ', '_') for _, f
                in campaign['types'].items()]
        if file_format == "csv":
            file_buffer = StringIO()
            data = []
            for feature in features:
                feature_json = S3Data().fetch(f'campaigns/{uuid}/{feature}.json')
                data += feature_json
            if username:
                data = [item for item in data if item['last_edited_by'] == username]
            headers = list(data[0].keys())
            for row in data:
                for item in row['attributes']:
                    if item not in headers:
                        headers.append(item)
                for item in row['missing_attributes']:
                    if item not in headers:
                        headers.append(item)
            data = filter_json(data, filters)
            if len(data) > 0:
                for row in data:
                    for item in row['attributes']:
                        row[item] = 1
                    for item in row['missing_attributes']:
                        row[item] = 0
            headers.remove('missing_attributes')
            headers.remove('attributes')
            for col in headers:
                for row in data:
                    if col not in row:
                        row[col] = ''
            for d in data:
                del d['attributes']
            for d in data:
                del d['missing_attributes']
            return data
            writer = csv.DictWriter(file_buffer,fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
            mimetype = 'text/csv'
            response_file = BytesIO()
            file_buffer.seek(0)
            response_file.write(file_buffer.getvalue().encode('utf-8'))
            response_file.seek(0)
        if file_format == "osm":
            file_buffer = BytesIO()
            mimetype = 'text/xml'
            s3 = S3Data().s3
            xmls = []
            for feature in features:
                key = f'campaigns/{uuid}/overpass/{feature}.xml'
                data = s3.get_object(Bucket=S3Data().bucket, Key=key)['Body'].read()
                data = filter_xml(data, filters)
                xmls.append(data)
            data = merge_xml(xmls)
            file_buffer.write(data)
            file_buffer.seek(0)
            response_file = file_buffer
        if file_format == None:
            return
        feature_name = "all_features"
        if username:
            feature_name = username

        resp = send_file(response_file,
                    as_attachment=True,
                    attachment_filename=f'{feature_name}.{file_format}',
                    mimetype=mimetype)
        return resp


class DownloadFeature(Resource):
    """ download feature list """

    def post(self, uuid, feature_name):
        parser = reqparse.RequestParser()
        parser.add_argument('fileFormat', type=str)
        parser.add_argument('filter', type=dict)
        args = parser.parse_args()
        file_format = args.get('fileFormat', None)
        filters = args.get('filter', {})
        if file_format == "csv":
            file_buffer = StringIO()
            data = S3Data().fetch(f'campaigns/{uuid}/{feature_name}.json')
            headers = list(data[0].keys())
            data = filter_json(data, filters)
            if len(data) > 0:
                for item in data[0]['attributes']:
                    headers.append(item)
                for item in data[0]['missing_attributes']:
                    headers.append(item)
                for row in data:
                    for item in row['attributes']:
                        row[item] = 1
                    for item in row['missing_attributes']:
                        row[item] = 0
            headers.remove('missing_attributes')
            headers.remove('attributes')
            for d in data:
                del d['attributes']
            for d in data:
                del d['missing_attributes']
            writer = csv.DictWriter(file_buffer,fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
            mimetype = 'text/csv'
            response_file = BytesIO()
            file_buffer.seek(0)
            response_file.write(file_buffer.getvalue().encode('utf-8'))
            response_file.seek(0)
        if file_format == "osm":
            file_buffer = BytesIO()
            mimetype = 'text/xml'
            s3 = S3Data().s3
            key = f'campaigns/{uuid}/overpass/{feature_name}.xml'
            data = s3.get_object(Bucket=S3Data().bucket, Key=key)['Body'].read()
            data = filter_xml(data, filters)
            file_buffer.write(data)
            file_buffer.seek(0)
            response_file = file_buffer
        if file_format == None:
            return
        resp = send_file(response_file,
                    as_attachment=True,
                    attachment_filename=f'{feature_name}.{file_format}',
                    mimetype=mimetype)
        return resp


# Setup the Api resource routing here
api.add_resource(
        CampaignList,
        '/campaigns')
api.add_resource(
        UserCampaigns,
        '/user/<string:osm_id>/campaigns')
api.add_resource(
        CampaignTagList,
        '/campaigns/<string:tag>')
api.add_resource(
        CampaignNearestList,
        '/nearest_campaigns/<string:campaign_status>')
api.add_resource(
        CampaignNearestWithTagList,
        '/nearest_campaigns/<string:coordinate>/<string:tag>')
api.add_resource(
        CampaignTotal,
        '/total_campaigns')
api.add_resource(
        CampaignContributors,
        '/campaign/total_contributors/<string:uuid>/<string:feature>')
api.add_resource(
        PDFBundle,
        '/campaigns/<string:uuid>/pdfs')
api.add_resource(
        PDFBundleById,
        '/campaigns/<string:uuid>/pdfs/<string:grid_id>')
api.add_resource(
        UserSearch,
        '/user-search/<string:name>')
api.add_resource(
        AllFeatures,
        '/campaigns/<string:uuid>/feature-types')
api.add_resource(
        GetFeature,
        '/campaigns/<string:uuid>/feature-types/<string:feature_name>')
api.add_resource(
        DownloadFeatures,
        '/campaigns/<string:uuid>/download')
api.add_resource(
        DownloadFeature,
        '/campaigns/<string:uuid>/download/<string:feature_name>')

