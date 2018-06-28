#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Table,
    Text,
    ForeignKey,
    Date,
    DateTime,
    BOOLEAN
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import and_, or_
from sqlalchemy.sql.expression import true
from geoalchemy2 import Geometry


db_location = os.environ['DATABASE_URL']
engine = create_engine(db_location, echo=True)


Base = declarative_base()

Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
session = Session()


adminAssociations = Table(
    'adminAssociations',
    Base.metadata,
    Column(
        'user_id',
        Integer,
        ForeignKey('user.id'),
        primary_key=True
        ),
    Column(
        'campaign_id',
        Integer,
        ForeignKey('campaign.id'),
        primary_key=True
        )
    )

typeCampaignAssociations = Table(
    'typeCampaignAssociations',
    Base.metadata,
    Column(
        'campaign_id',
        Integer,
        ForeignKey('campaign.id'),
        primary_key=True
        ),
    Column(
        'type_id',
        Integer,
        ForeignKey('featureType.id'),
        primary_key=True
        )
    )

featureTypeAssociations = Table(
    'featureTypeAssociations',
    Base.metadata,
    Column(
        'feature_id',
        Integer,
        ForeignKey('attribute.id'),
        primary_key=True
        ),
    Column(
        'type_id',
        Integer,
        ForeignKey('featureType.id'),
        primary_key=True
        )
    )

teamUserAssociations = Table(
    'teamUserAssociations',
    Base.metadata,
    Column(
        'user_id',
        Integer,
        ForeignKey('user.id'),
        primary_key=True
        ),
    Column(
        'team_id',
        Integer,
        ForeignKey('team.id'),
        primary_key=True
        )
    )

functionCampaignAssociations = Table(
    'functionCampaignAssociations',
    Base.metadata,
    Column(
        'campaign_id',
        Integer,
        ForeignKey('campaign.id')
        ),
    Column(
        'function_id',
        Integer,
        ForeignKey('function.id')
        )
    )


class User(Base):

    __tablename__ = 'user'

    id = Column(
        'id',
        Integer,
        primary_key=True,
        autoincrement=True
        )
    osm_user_id = Column(
        String(20),
        unique=True,
        nullable=False
        )
    email = Column(String(40))
    campaign_creator = relationship(
        'Campaign',
        back_populates='creator',
        lazy=True,
        uselist=False
        )
    chat_sender = relationship(
        'Chat',
        foreign_keys='Chat.sender_id',
        back_populates='sender',
        lazy=True,
        uselist=False
        )
    chat_receiver = relationship(
        'Chat',
        foreign_keys='Chat.receiver_id',
        back_populates='reciever',
        lazy=True,
        uselist=False
        )
    notification_sender = relationship(
        'Notification',
        back_populates='sender',
        lazy=True,
        uselist=False
        )
    campaigns = relationship(
        'Campaign',
        secondary=adminAssociations,
        lazy='subquery',
        back_populates='users'
        )
    teams = relationship(
        'Team',
        secondary=teamUserAssociations,
        lazy='subquery',
        back_populates='users'
        )

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def create(self):
        """ Creates and Saves the current model the DB """
        session.add(self)
        session.commit()

    def save(self):
        session.commit()

    def get_by_osm_id(self, osm_id):
        """ Returns the user with the specified osm user id """
        return session.query(User).filter(
            User.osm_user_id == osm_id
            ).first()

    def get_all(self):
        """ Returns all the users registered with field-campaigner """
        return session.query(User).all()

    def update(self, user_dto):
        """ Updates the user's details """
        if user_dto['osm_user_id']:
            self.osm_user_id = user_dto['osm_user_id']
        if user_dto['email']:
            self.email = user_dto['email']
        session.commit()


class Campaign(Base):

    __tablename__ = 'campaign'

    id = Column(
        'id',
        Integer,
        primary_key=True,
        autoincrement=True
        )
    creator_id = Column(
        Integer,
        ForeignKey('user.id'),
        nullable=False
        )
    creator = relationship(
        'User',
        back_populates='campaign_creator'
        )
    users = relationship(
        'User',
        secondary=adminAssociations,
        lazy='subquery',
        back_populates='campaigns'
        )
    feature_types = relationship(
        'FeatureType',
        secondary=typeCampaignAssociations,
        lazy='subquery',
        back_populates='campaigns'
        )
    functions = relationship(
        'Function',
        secondary=functionCampaignAssociations,
        lazy='subquery',
        back_populates='campaigns'
        )
    chat = relationship(
        'Chat',
        back_populates='campaign',
        lazy=True
        )
    notification = relationship(
        'Notification',
        back_populates='campaign',
        lazy=True
        )
    geometry = Column(Geometry('POLYGON'))
    task_boundaries = relationship(
        'TaskBoundary',
        back_populates='campaign',
        lazy=True
        )
    name = Column(
        String(20),
        unique=True,
        nullable=False
        )
    description = Column(String(200))
    start_date = Column(
        Date(),
        nullable=False
        )
    end_date = Column(
        Date(),
        nullable=False
        )
    create_on = Column(
        DateTime(),
        nullable=False
        )
    link_to_OpenMapKit = Column(
        BOOLEAN(),
        default=False
        )
    version = Column(Integer)
    uuid = Column(String(100))
    remote_projects = Column(String(30))
    map_type = Column(String(20))
    thumbnail = Column(String(100))

    def __init__(self, **kwargs):
        super(Campaign, self).__init__(**kwargs)

    def create(self):
        """ Creates and saves the current model to DB """
        session.add(self)
        session.commit()

    def save(self):
        session.commit()

    def get_by_uuid(self, uuid):
        """ Returns the campaign object based on the uuid """
        return session.query(Campaign).filter(Campaign.uuid == uuid).first()

    def get_all(self):
        """ Returns all the campaigns in the DB """
        return session.query(Campaign).all()

    def get_all_active(self):
        """ Returns all the active campaigns """
        from datetime import datetime
        date = datetime.now()
        return session.query(Campaign).filter(
            and_(
                Campaign.start_date <= date,
                date <= Campaign.end_date)
            ).all()

    def get_all_inactive(self):
        """ Returns all the inactive campaigns """
        from datetime import datetime
        date = datetime.now()
        return session.query(Campaign).filter(
            or_(Campaign.start_date >= date,
                date >= Campaign.end_date)
            ).all()

    def get_task_boundary(self):
        """ Returns the task_boundary of the campaign """
        return session.query(TaskBoundary).filter(
            TaskBoundary.campaign_id == self.id
            ).first()

    def get_task_boundary_as_geoJSON(self):
        """ Returns the task boundary in GeoJSON format """
        return session.query(
            TaskBoundary.coordinates.ST_AsGeoJSON()
            ).filter(
            TaskBoundary.campaign_id == self.id
            ).first()

    def update(self, campaign_dto):
        """ Updates and saves the model object """
        from datetime import datetime
        if campaign_dto['name']:
            self.name = campaign_dto['name']
        if campaign_dto['description']:
            self.description = campaign_dto['description']
        if campaign_dto['start_date']:
            self.start_date = campaign_dto['start_date']
        if campaign_dto['end_date']:
            self.end_date = campaign_dto['end_date']
        self.create_on = datetime.now()
        session.commit()


class Chat(Base):

    __tablename__ = 'chat'

    id = Column(
        'id',
        Integer,
        primary_key=True,
        autoincrement=True
        )
    campaign_id = Column(
        Integer,
        ForeignKey('campaign.id'),
        nullable=False
        )
    campaign = relationship(
        'Campaign',
        back_populates='chat'
        )
    sender_id = Column(
        Integer,
        ForeignKey('user.id'),
        nullable=False
        )
    sender = relationship(
        'User',
        foreign_keys=[sender_id],
        back_populates='chat_sender'
        )
    receiver_id = Column(
        Integer,
        ForeignKey('user.id'),
        nullable=False
        )
    reciever = relationship(
        'User',
        foreign_keys=[receiver_id],
        back_populates='chat_receiver'
        )
    message = Column(String(200))
    send_time = Column(DateTime())
    delivered = Column(
        BOOLEAN(),
        default=False
        )

    def __init__(self, **kwargs):
        super(Chat, self).__init__(**kwargs)


class Notification(Base):

    __tablename__ = 'notification'

    id = Column(
        'id',
        Integer,
        primary_key=True,
        autoincrement=True
        )
    campaign_id = Column(
        Integer,
        ForeignKey('campaign.id'),
        nullable=False
        )
    campaign = relationship(
        'Campaign',
        back_populates='notification'
        )
    sender_id = Column(
        Integer,
        ForeignKey('user.id'),
        nullable=False
        )
    sender = relationship(
        'User',
        back_populates='notification_sender'
        )
    notification_message = Column(String(100))
    time = Column(DateTime())
    delivered = Column(
        BOOLEAN(),
        default=False
        )

    def __init__(self, **kwargs):
        super(Notification, self).__init__(**kwargs)


class FeatureTemplate(Base):

    __tablename__ = 'featureTemplate'

    id = Column(
        'id',
        Integer,
        primary_key=True,
        autoincrement=True
        )
    name = Column(
        String(20),
        nullable=False
        )
    description = Column(String(200))
    featureType_id = Column(
        Integer,
        ForeignKey('featureType.id')
        )
    feature_type = relationship(
        'FeatureType',
        back_populates='feature_template'
        )

    def __init__(self, **kwargs):
        super(FeatureTemplate, self).__init__(**kwargs)


class FeatureType(Base):

    __tablename__ = 'featureType'

    id = Column(
        'id',
        Integer,
        primary_key=True,
        autoincrement=True
        )
    feature = Column(
        String(20),
        nullable=False
        )
    name = Column(String(20))
    is_template = Column(
        BOOLEAN(),
        default=False
        )
    feature_template = relationship(
        'FeatureTemplate',
        back_populates='feature_type'
        )
    function = relationship(
        'Function',
        back_populates='types',
        lazy=True
        )
    campaigns = relationship(
        'Campaign',
        secondary=typeCampaignAssociations,
        lazy='subquery',
        back_populates='feature_types'
        )
    attributes = relationship(
        'Attribute',
        secondary=featureTypeAssociations,
        lazy='subquery',
        back_populates='feature_types'
        )

    def __init__(self, **kwargs):
        super(FeatureType, self).__init__(**kwargs)

    def get_templates(self):
        """ Returns the templates feature types """
        return session.query(FeatureType).filter(
            FeatureType.is_template == true()
            ).all()

    def create(self):
        """ Creates and saves the current model to DB """
        session.add(self)
        session.commit()


class Attribute(Base):

    __tablename__ = 'attribute'

    id = Column(
        'id',
        Integer,
        primary_key=True,
        autoincrement=True
        )
    attribute_name = Column(String(20))
    feature_types = relationship(
        'FeatureType',
        secondary=featureTypeAssociations,
        lazy='subquery',
        back_populates='attributes'
        )

    def __init__(self, **kwargs):
        super(Attribute, self).__init__(**kwargs)

    def create(self):
        """ Creates and saves the current model to DB """
        session.add(self)
        session.commit()


class TaskBoundary(Base):

    __tablename__ = 'taskBoundary'

    id = Column(
        'id',
        Integer,
        primary_key=True,
        autoincrement=True
        )
    coordinates = Column(Geometry('POLYGON'))
    name = Column(String(100))
    status = Column(String(100))
    type_boundary = Column(String(100))
    team = relationship(
        'Team',
        back_populates='boundary',
        lazy=True,
        uselist=False
        )
    campaign_id = Column(
        Integer,
        ForeignKey('campaign.id'),
        nullable=False
        )
    campaign = relationship(
        'Campaign',
        back_populates='task_boundaries',
        lazy=True
        )

    def __init__(self, **kwargs):
        super(TaskBoundary, self).__init__(**kwargs)

    def create(self):
        """ Creates and saves the current model to DB """
        session.add(self)
        session.commit()


class Team(Base):

    __tablename__ = 'team'

    id = Column(
        'id',
        Integer,
        primary_key=True,
        autoincrement=True
        )
    name = Column(
        String(20),
        nullable=False
        )
    boundary_id = Column(
        Integer,
        ForeignKey('taskBoundary.id'),
        nullable=False
        )
    boundary = relationship(
        'TaskBoundary',
        back_populates='team'
        )
    users = relationship(
        'User',
        secondary=teamUserAssociations,
        lazy='subquery',
        back_populates='teams'
        )

    def __init__(self, **kwargs):
        super(Team, self).__init__(**kwargs)

    def create(self):
        """ Creates and saves the current model to DB """
        session.add(self)
        session.commit()

    def get_all(self):
        """ Returns all the teams registered in field campaigner """
        return session.query(Team).all()


class Function(Base):

    __tablename__ = 'function'

    id = Column(
        'id',
        Integer,
        primary_key=True,
        autoincrement=True
        )
    name = Column(
        String(100),
        nullable=False
        )
    feature = Column(String(100))
    type_id = Column(
        Integer,
        ForeignKey('featureType.id'),
        nullable=False
        )
    types = relationship(
        'FeatureType',
        back_populates='function'
        )
    campaigns = relationship(
        'Campaign',
        secondary=functionCampaignAssociations,
        lazy='subquery',
        back_populates='functions'
        )

    def __init__(self, **kwargs):
        super(Function, self).__init__(**kwargs)

    def create(self):
        """ Creates and saves the current model to DB """
        session.add(self)
        session.commit()
