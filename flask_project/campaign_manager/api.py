import os
import http.client
import json
from flask_restful import Resource, Api
from flask import request, send_file

from io import BytesIO
import boto3
import json
from zipfile import ZipFile

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
        campaign = S3Data().fetch(f'campaigns/{uuid}/campaign.json')
        features = [campaign['types'][f'type-{i + 1}']['type'] for i, 
                    feature in enumerate(campaign['types'])]
        all_features = []
        for feature in features:
            feature_json = S3Data().fetch(f'campaigns/{uuid}/{feature}.json')
            all_features += feature_json
        return all_features


class ContributorFeatures(Resource):
    """ get all features in a campaign by username"""

    def get(self, uuid, username):
        campaign = S3Data().fetch(f'campaigns/{uuid}/campaign.json')
        features = [campaign['types'][f'type-{i + 1}']['type'] for i,
                    feature in enumerate(campaign['types'])]
        all_features = []
        for feature in features:
            feature_json = S3Data().fetch(f'campaigns/{uuid}/{feature}.json')
            all_features += feature_json
        user_features = [f for f in all_features if f['last_edited_by'] == username]
        return user_features


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
        ContributorFeatures,
        '/campaigns/<string:uuid>/feature-types/<string:username>')
