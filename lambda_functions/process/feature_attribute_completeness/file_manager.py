import os
import boto3
import gzip
import shutil
from tempfile import TemporaryFile


class FileManager(object):
    SIZE_LIMIT = 5000000

    def __init__(self, destination):
        self.count = 1
        self.location = '/tmp'
        self.destination = destination
        self.fd = None
        self.open()

    def current_file(self):
        return "{location}/{filename}_{count}.{extension}".format(
            location=self.location,
            filename=self.filename,
            count=self.count,
            extension=self.extension)

    def current_key(self):
        return "{destination}/{filename}_{count}.{extension}".format(
            destination=self.destination,
            filename=self.filename,
            count=self.count,
            extension=self.extension)

    def open(self):
        self.fd = open(self.current_file(), 'w')
        self.write_header()

    def close(self):
        self.write_footer()
        self.fd.close()

    def size(self):
        return os.stat(self.current_file()).st_size

    def remove_last_comma(self):
        # if self.size() > 2:
        self.fd.seek(0, 2)  # go to end of file
        self.fd.seek(self.fd.tell() - 2, 0)  # go backwards 2 bytes

    def write(self, data):
        if (self.size() + len(data)) >= self.SIZE_LIMIT:
            self.close()
            self.save()
            self.remove()
            self.count += 1
            self.open()

        self.fd.write(data)
        self.fd.write(',\n')

    def save(self):
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(os.environ['S3_BUCKET'])

        with open(self.current_file(), 'rb') as json_file, TemporaryFile() as temp_file:
            with gzip.GzipFile(fileobj=temp_file, mode='wb') as gz:
                shutil.copyfileobj(json_file, gz)
            temp_file.seek(0)

            bucket.upload_fileobj(
                Fileobj=temp_file,
                Key=self.current_key(),
                ExtraArgs={
                    "ACL": "public-read",
                    "ContentType": "application/json",
                    "ContentEncoding": "gzip"
                })

    def remove(self):
        os.remove(self.current_file())


class ErrorsFileManager(FileManager):
    def __init__(self, destination):
        self.filename = 'errors'
        self.extension = 'json'
        super(ErrorsFileManager, self).__init__(destination)

    def write_header(self):
        self.fd.write('[\n')

    def write_footer(self):
        self.remove_last_comma()
        self.fd.write(']')


class GeojsonFileManager(FileManager):
    def __init__(self, destination):
        self.filename = 'geojson'
        self.extension = 'json'
        super(GeojsonFileManager, self).__init__(destination)

    def write_header(self):
        self.fd.write('{"type": "FeatureCollection","features": [\n')

    def write_footer(self):
        self.remove_last_comma()
        self.fd.write(']}')
