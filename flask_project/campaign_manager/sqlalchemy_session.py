import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app_sockets import osm_app

osm_app.config.from_object(os.environ['APP_SETTINGS'])
engine = create_engine(osm_app.config['DB_LOCATION'])

Base = declarative_base()

Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
session = Session()
