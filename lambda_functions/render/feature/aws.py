import os
import json
from dependencies import yaml
import boto3


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
            print("> TRY")
            obj = self.s3.get_object(
                Bucket=self.bucket,
                Key=key)
        except:
            return []

        raw_content = obj['Body'].read() # binary string
        # try: raw_content = obj['Body'].read().decode('utf-8')
        print(f"key: {key}")
        print(f"raw_content: {raw_content}")
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
            print("> IF")
            content = json.loads(raw_content)
            print(f"content: {content}")
            return content
        else:
            print("> ELSE")
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
            print("TRUE")
            return True
        print("FALSE")
        return False

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
