from models.models import *

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
