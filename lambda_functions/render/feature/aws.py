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
        print("> Calling save function")
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
        objects = []
        req_kwargs = {'Bucket': self.bucket, 'Prefix': prefix}

        # Loop to get all campaigns.
        while True:
            try:
                resp = self.s3.list_objects_v2(**req_kwargs)
                contents = resp['Contents']
            except KeyError:
                break

            for obj in contents:
                if obj['Key'] != prefix:
                    key = obj['Key'].replace(prefix, '').split('/')[0]
                    if key in [o['uuid'] for o in objects]:
                        continue
                    modified = obj['LastModified'].toordinal()

                    # Include also last_modified to check cache.
                    data_dict = {'uuid': key, 'modified': modified}
                    objects.append(data_dict)

            # Check that we are done getting data from s3.
            if resp['IsTruncated'] is False:
                break

            # Update request with continuation token returned from response.
            new_dict = {'ContinuationToken': resp['NextContinuationToken']}
            req_kwargs.update(new_dict)

        return objects
