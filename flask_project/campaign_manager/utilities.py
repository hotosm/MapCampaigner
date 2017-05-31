__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '16/05/17'

import os
from utilities import absolute_path
import time

from reporter.osm import fetch_osm

def module_path(*args):
    """Get an absolute path for a file that is relative to the root.

    :param args: List of path elements.
    :type args: list

    :returns: An absolute path.
    :rtype: str
    """
    return os.path.join(absolute_path(), 'campaign_manager')


def temporary_folder():
    """Get an absolute path for temp folder which
    is relative to the root."""

    return os.path.join(
        module_path(),
        'campaigns_data',
        'temp'
    )


def get_osm_user():
    osm_user_path = os.path.join(
        module_path(), 'osm_user.txt')
    with open(osm_user_path) as f:
        content = f.readlines()
    users = [x.strip() for x in content]
    users.sort()
    return users


def get_tags():
    osm_user_path = os.path.join(
        module_path(), 'tag_data.txt')
    with open(osm_user_path) as f:
        content = f.readlines()
    tags = [x.strip() for x in content]
    tags.sort()
    return tags


def load_osm_document_cached(file_path, url_path):
    """Load an cached osm document, update the results if 15 minutes old.

    :type file_path: basestring
    :param file_path: The path on the filesystem

    :param url_path: Path of the file
    :type url_path: str

    :returns: A file object for the the downloaded file.
    :rtype: file
    """
    elapsed_seconds = 0
    limit_seconds = 900 # 15 minutes
    if os.path.exists(file_path):
        current_time = time.time()  # in unix epoch
        file_time = os.path.getmtime(file_path)  # in unix epoch
        elapsed_seconds = current_time - file_time
        if elapsed_seconds > limit_seconds:
            os.remove(file_path)
    if elapsed_seconds > limit_seconds or not os.path.exists(file_path):
        fetch_osm(file_path, url_path)
    file_handle = open(file_path, 'rb')
    return file_handle
