import os
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from app import osm_app, db


osm_app.config.from_object(os.environ['APP_SETTINGS'])

migrate = Migrate(osm_app, db)
manager = Manager(osm_app)

manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
