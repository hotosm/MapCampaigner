import os
from flask_script import Manager

from app import osm_app
from campaign_manager.script.generate_geometry import (
    generate_geometry as generate_geometry_script
)

osm_app.config.from_object(os.environ['APP_SETTINGS'])

manager = Manager(osm_app)


@manager.command
def generate_geometry():
    generate_geometry_script()


if __name__ == '__main__':
    manager.run()
