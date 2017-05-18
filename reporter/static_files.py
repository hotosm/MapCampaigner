# coding=utf-8
"""Helper module for serving static files when running in dev mode.
:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""
import os
from flask import abort, Response

#
# These are only used to serve static files when testing
#
file_suffix_to_mimetype = {
    '.css': 'text/css',
    '.jpg': 'image/jpeg',
    '.html': 'text/html',
    '.ico': 'image/x-icon',
    '.png': 'image/png',
    '.js': 'application/javascript'
}


def static_file(path):
    """Flask static file hander used for local testing.

    :param path: Path for the static resource to be served.
    :type path: str

    :returns: An http Response of the correct mime type for the resource
            requested.
    :rtype: HttpResponse
    """
    try:
        f = open(path)
    except IOError:
        abort(404)
        return
    _, ext = os.path.splitext(path)
    if ext in file_suffix_to_mimetype:
        return Response(f.read(), mimetype=file_suffix_to_mimetype[ext])
    return f.read()
