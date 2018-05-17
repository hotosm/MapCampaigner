"""The current name of the file is ambiguous with the work it does.
The name needs to corrected after all the different forks are merged,
the file stores additional functions like sockets, celery etc. and
removes circular dependecies.
"""
from flask import Flask
from flask_socketio import SocketIO
from flask_mail import Mail

osm_app = Flask(__name__, static_folder='./campaign_manager/static')
osm_app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
socketio = SocketIO(osm_app)

osm_app.config.update(dict(
    DEBUG=True,
    # email server
    MAIL_SERVER='smtp.googlemail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    # MAIL_USERNAME = "Client's email address",
    # MAIL_PASSWORD = "Client's email password",
))

mail = Mail(osm_app)
