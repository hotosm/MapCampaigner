import os
import boto3
import json
from dependencies import yaml


class S3Data(object):
    """
    Class for AWS S3
    """

    def __init__(self):
        """
        Initialize the s3 client.
        """
        self.s3 = boto3.client('s3')
        self.bucket = os.environ['S3_BUCKET']

    def fetch(self, key):
        """
        Fetch a S3 object from
        :param key: path + filename
        :type key: string

        :returns: content of the file (json/yaml)
        :rtype: dict
        """
        try:
            obj = self.s3.get_object(
                Bucket=self.bucket,
                Key=key)
        except:
            return []

        raw_content = obj['Body'].read()
        return self.load(raw_content, key)

    def load(self, raw_content, key):
        """
        Load json or yaml content.

        :param raw_content: json/yaml raw_content
        :type raw_content: bytes

        :param key: path + filename
        :type key: string

        :returns: content of the file (json/yaml)
        :rype: dict
        """
        if self.is_json(key):
            return json.loads(raw_content)
        else:
            return yaml.load(raw_content)

    def is_json(self, key):
        """
        Check if the key has a json/geojson extension.

        :param key: path + filename
        :type key: string

        :returns: True or False
        :rtype: boolean
        """
        if key.split('.')[-1] in ['json', 'geojson']:
            return True
        return False

    def download_file(self, key, type_id, destination):
        with open('/{destination}/{type_id}.xml'.format(
            type_id=type_id,
            destination=destination), 'wb') as data:
            self.s3.download_fileobj(
                Bucket=self.bucket,
                Key=key,
                Fileobj=data)

    def upload_file(self, key, body):
        self.s3.upload_fileobj(
            Fileobj=body,
            Bucket=self.bucket,
            Key=key,
            ExtraArgs={
                'ACL': 'public-read'
            })

    def create(self, key, body):
        """
        Create an object in the S3 bucket.

        :param key: path + filename
        :type key: string

        :param body: content of the file
        :type body: string

        :returns:
        """
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body,
            ACL='public-read')

    def get_last_modified_date(self, key):
        obj = self.s3.get_object(
            Bucket=self.bucket,
            Key=key)
        return obj['LastModified']
