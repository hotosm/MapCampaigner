import os
import json
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
        try:
            for obj in self.s3.list_objects(
                Bucket=self.bucket,
                Prefix=prefix)['Contents']:
                if obj['Key'] != prefix:
                    key = obj['Key'].replace(prefix, '')
                    objects.append(key.split('/')[0])
            return list(set(objects))
        except KeyError:
            return []

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

    def delete(self, key):
        """
        Delete a key in the S3 bucket.

        :param key: pathname + filename
        :type key: string

        :returns:
        """
        self.s3.delete_object(
            Bucket=self.bucket,
            Key=key)