# -*- coding:utf-8 -*-
"""Configuration options for the osm reporter app.
:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""
# List of OSM pseudos
CREW = []
# Default bbox
BBOX = '20.411482,-34.053726,20.467358,-34.009483'
# Whether to display the "update stats control" on the map
DISPLAY_UPDATE_CONTROL = True
# Where to store OSM files
CACHE_DIR = '/tmp'
# Default object type
TAG_NAMES = [
    'building',  # first is default
    'highway',
]
# Options for the osm2pgsql command line
OSM2PGSQL_OPTIONS = ''
