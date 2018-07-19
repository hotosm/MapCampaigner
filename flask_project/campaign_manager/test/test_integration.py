import os
import unittest
import ast
import json

from bs4 import BeautifulSoup
from flask import abort, url_for, Flask
from flask_testing import TestCase
from geoalchemy2.shape import from_shape
from shapely.geometry import asShape
from datetime import date, datetime

from campaign_manager.models.models import (
    User,
    Campaign,
    FeatureType,
    FeatureTemplate,
    Team,
    Function,
    TaskBoundary)
from app import osm_app
from campaign_manager.sqlalchemy_session import session, Base, engine


""" Geometry object for mock campaign """
geom = {
    "type": "Polygon",
    "coordinates": [
        [
            [
                -22.7271314710379,
                23.9871672761574],
            [
                -22.7271314710379,
                23.9879122455024],
            [
                -22.7264448255301,
                23.9879122455024],
            [
                -22.7264448255301,
                23.9871672761574],
            [
                -22.7271314710379,
                23.9871672761574]
        ]
    ]
}


class TestBase(TestCase):
    """Base Class for the test-classes to inherit from.
    Contains configuration and setup functions for the tests.
    """

    def create_app(self):
        """ Test Configurations. """
        osm_app.config.from_object('app_config.TestingConfig')
        return osm_app

    def setUp(self):
        """ Creates a DB for testing.
        Will be called before every test.
        """
        session.commit()
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    def tearDown(self):
        """ Destroys the DB.
        Will be called after every test.
        """
        session.rollback()
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)


class TestViews(TestBase):

    def test_404_view(self):
        """ Test the 404 page is avaible when url resolver not found."""
        response = self.client.get(
            '/url-not-exists',
            content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b'The page you are looking for could not be found',
            response.data)

    def test_home_view(self):
        """ Test the homepage view is accessible without login."""
        response = self.client.get('/', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Monitor Field Mapping in OpenStreetMap', response.data)

    def test_create_view(self):
        """ Test that a user is able to access create campaign view."""
        response = self.client.get('/campaign/new', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        message = (
            b'Provide more detail about which features the campaign '
            b'will  collect')
        self.assertIn(message, response.data)

    def test_campaign_detail_view(self):
        """ Test that a created campaign is visible without login.
        """
        # create mock user
        mock_user = User(
            osm_user_id="user_new",
            email="email@gmail.com")
        mock_user.create()

        # create mock campaign
        mock_campaign = Campaign(
            creator_id=mock_user.id,
            name="new",
            description="campaign_description",
            start_date=date(2018, 1, 1),
            end_date=date(2018, 1, 1),
            create_on=datetime.now(),
            uuid="mock_campaign_uuid")
        mock_campaign.create()

        # create mock feature type
        mock_feature_type = FeatureType(
            feature="feature",
            name="feature_name")
        mock_feature_type.create()

        # create mock template feature
        mock_feature_type = FeatureType(
            feature="template",
            name="feature_name",
            is_template=True)
        mock_feature_type.create()
        mock_feature_template = FeatureTemplate(
            name="Template",
            description="Template_description",
            featureType_id=mock_feature_type.id)
        mock_feature_template.create()

        # create mock taskboundary
        geom_obj = from_shape(asShape(geom), srid=4326)
        mock_taskBoundary = TaskBoundary(
            coordinates=geom_obj,
            name="name",
            status="status",
            type_boundary="type_boundary",
            campaign_id=mock_campaign.id)
        mock_taskBoundary.create()

        # create mock team
        mock_team = Team(
            name="Team7",
            boundary_id=mock_taskBoundary.id)
        mock_team.create()

        # create mock function
        mock_function = Function(
            name="Function1",
            feature="data_collection",
            type_id=mock_feature_type.id)
        mock_function.create()

        response = self.client.get(
            '/campaign/mock_campaign_uuid',
            content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'new', response.data)

    def test_about_view(self):
        """ Test that about view is accessible without logging."""
        response = self.client.get('/about', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Who built this project?', response.data)

    def test_resource_view(self):
        """ Test that resource view is accessible without logging."""
        response = self.client.get('/resources', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'RESOURCES', response.data)
