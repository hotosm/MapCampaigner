# coding=utf-8
"""OSM Reporter exceptions.
:copyright: (c) 2016 by Etienne Trimaille
:license: GPLv3, see LICENSE for more details.
"""


class OverpassTimeoutException(Exception):
    pass


class OverpassBadRequestException(Exception):
    pass


class OverpassConcurrentRequestException(Exception):
    pass


class OverpassDoesNotReturnData(Exception):
    pass
