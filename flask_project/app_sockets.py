"""The current name of the file is ambiguous with the work it does.
The name needs to corrected after all the different forks are merged,
the file stores additional functions like sockets, celery etc. and
removes circular dependecies.
"""
from flask import Flask

osm_app = Flask(__name__, static_folder='./campaign_manager/static')
