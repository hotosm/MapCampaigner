import json
import yaml
import boto3
from app_config import Config

class S3Data(object):
    """
    Class for AWS S3
    """

    def __init__(self):
        """
        Initialize the s3 client.
        """
        self.s3 = boto3.client('s3')


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
                Bucket=Config.AWS_BUCKET, 
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


    def list(self, prefix):
        """
        List S3 objects in bucket starting with prefix.

        There aren't files or folders in a S3 bucket, only objects.
        A key is the name of an object. The key is used to retrieve an object.

        examples of keys: 
        - campaign/
        - campaign/uuid.json
        - campaign/uuid.geojson
        - surveys/
        - surveys/buildings
        - kartoza.jpg

        :param prefix: keys has to start with prefix.
        :type prefix: string

        :returns: list of keys starting with prefix in the bucket.
        :rtype: list
        """
        prefix = '{}/'.format(prefix)

        objects = []
        for obj in self.s3.list_objects(
            Bucket=Config.AWS_BUCKET,
            Prefix=prefix)['Contents']:
            if obj['Key'] != prefix:
                objects.append(obj['Key'].replace(prefix, ''))
        return objects

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
            Bucket=Config.AWS_BUCKET,
            Key=key,
            Body=body)
