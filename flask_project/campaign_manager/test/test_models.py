import os
import ast
import datetime

from flask_testing import TestCase
from flask import Flask
from geoalchemy2.shape import from_shape
from shapely.geometry import asShape
from sqlalchemy import select, func
from sqlalchemy.orm import sessionmaker
from campaign_manager.models.models import (
    User,
    Campaign,
    FeatureType,
    FeatureTemplate,
    TaskBoundary,
    Tag,
    Team,
    Function)
from campaign_manager.sqlalchemy_session import engine, session, Base


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
        app = Flask(__name__)
        return app

    def setUp(self):
        """ Creates a DB for testing.
        Will be called before every test.
        """
        session.commit()
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

        # create mock user
        mock_user = User(
            osm_user_id="user_new",
            email="email@gmail.com")
        mock_user.create()

        # create mock campaign
        mock_campaign = Campaign(
            creator_id=mock_user.id,
            name="campaign_new",
            description="campaign_description",
            start_date=datetime.date(2018, 1, 1),
            end_date=datetime.date(2018, 1, 1),
            create_on=datetime.datetime.now(),
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

    def tearDown(self):
        """ Destroys the DB.
        Will be called after every test.
        """
        for tbl in reversed(Base.metadata.sorted_tables):
            engine.execute(tbl.delete())
        Base.metadata.create_all(engine)


class TestUser(TestBase):
    """Tests for Table: User."""

    def test_01_user_name(self):
        """Tests that a new user is created in the DB."""
        mock_user = User().get_by_osm_id("user_new")
        count_user = session.query(User).count()
        self.assertEqual(count_user, 1)

    def test_02_update_user_email(self):
        """Tests the User object attributes can be updated."""
        mock_user = User().get_by_osm_id("user_new")
        user_dto = dict(
            email="new_email@gmail.com"
            )
        mock_user.update(user_dto)
        self.assertEqual(mock_user.email, "new_email@gmail.com")

    def test_03_delete_user(self):
        """Tests User object can be deleted from the DB."""
        mock_user = User().get_by_osm_id("user_new")
        mock_campaign = Campaign().get_by_uuid("mock_campaign_uuid")
        mock_taskBoundary = TaskBoundary().get_first()
        mock_team = Team().get_first()
        mock_team.delete()
        mock_taskBoundary.delete()
        mock_campaign.delete()
        mock_user.delete()
        user_count = session.query(User).count()
        self.assertFalse(user_count, 0)


class TestCampaign(TestBase):
    """Tests for Table: Campaign."""

    def test_01_campaign_name(self):
        """Tests a new campaign is created in the DB."""
        mock_campaign = Campaign().get_by_uuid("mock_campaign_uuid")
        self.assertEqual(mock_campaign.name, "campaign_new")

    def test_02_campaign_creator(self):
        """Tests that campaign has a creator."""
        mock_campaign = Campaign().get_by_uuid("mock_campaign_uuid")
        self.assertEqual(mock_campaign.creator.osm_user_id, "user_new")

    def test_03_update_campaign(self):
        """Tests campaign object can be updated."""
        mock_campaign = Campaign().get_by_uuid("mock_campaign_uuid")
        campaign_dto = dict(
            name="new_campaign_name"
            )
        mock_campaign.update(campaign_dto)
        self.assertEqual(mock_campaign.name, "new_campaign_name")

    def test_04_geom_campaign(self):
        """Tests the campaign method returns GeoJson object."""
        mock_campaign = Campaign().get_by_uuid("mock_campaign_uuid")
        coor_geoJSON = mock_campaign.get_task_boundary_as_geoJSON()
        geom_check = (geom == ast.literal_eval(coor_geoJSON[0]))
        self.assertTrue(geom_check)

    def test_05_default_feild_condition(self):
        """Tests the default value of link_to_OpenMapKit field."""
        mock_campaign = Campaign().get_by_uuid("mock_campaign_uuid")
        self.assertFalse(mock_campaign.link_to_OpenMapKit)


class TestFeatureType(TestBase):
    """Tests for Table: FeatureType."""

    def test_01_featuretype_length(self):
        mock_feature_type = FeatureType().get_first()
        check_len = (len(mock_feature_type.name) < 20)
        self.assertTrue(check_len)

    def test_02_default_field(self):
        """Tests field's default value."""
        mock_feature_type = FeatureType().get_first()
        self.assertFalse(mock_feature_type.is_template)

    def test_03_tags(self):
        """Tests Tag-Feature relationship."""
        mock_feature_type = FeatureType().get_first()
        tag1 = Tag(
            name="tag1"
            )
        tag1.create()
        tag2 = Tag(
            name="tag2"
            )
        tag2.create()
        tag_list = [tag1, tag2]
        mock_feature_type.add_tags(tag_list)
        tags_obj = mock_feature_type.tags
        tags = [x.name for x in tags_obj]
        tag_check = (tags == ["tag1", "tag2"])
        self.assertTrue(tag_check)


class TestFeatureTemplate(TestBase):
    """Tests for Table: FeatureTemplate."""

    def test_01_is_template(self):
        """Tests the template condition for a feature."""
        mock_feature_type = session.query(FeatureType).all()
        mock_feature_type = mock_feature_type[1]
        self.assertTrue(mock_feature_type.is_template)

    def test_02_feature_template_name(self):
        """Tests a template Feature type is created in DB."""
        mock_feature_type = session.query(FeatureType).all()
        mock_feature_type = mock_feature_type[1]
        mock_feature_template = FeatureTemplate().get_first()
        self.assertEqual(mock_feature_template.name, "Template")


class TestTaskBoundary(TestBase):
    """Tests for Table: TaskBoundary."""

    def test_01_create_task_boundary(self):
        """Test taskboundary is created and contains the correct
        geoJSON data."""
        mock_task_boundary = TaskBoundary().get_first()
        coor_geoJSON = session.query(
            TaskBoundary.coordinates.ST_AsGeoJSON()
            ).first()
        geom_check = (geom == ast.literal_eval(coor_geoJSON[0]))
        self.assertTrue(geom_check)

    def test_02_task_boundary_geom_type(self):
        """Tests the type of GIS object."""
        mock_campaign = Campaign().get_by_uuid("mock_campaign_uuid")
        mock_geom_obj = mock_campaign.get_task_boundary_as_geoJSON()
        mock_geom_obj = ast.literal_eval(mock_geom_obj[0])
        self.assertEqual(mock_geom_obj['type'], "Polygon")


class TestTeam(TestBase):
    """Tests for Table: Team."""

    def test_01_create_team(self):
        """Tests a team is created in DB."""
        mock_team = Team().get_first()
        self.assertEqual(mock_team.name, "Team7")

    def test_02_update_team_name(self):
        """Tests team can be updated in DB."""
        mock_team = Team().get_first()
        team_dto = dict(
            name="new_team7"
            )
        mock_team.update(team_dto)
        self.assertEqual(mock_team.name, "new_team7")


class TestFunction(TestBase):
    """Tests for Table: Function."""

    def test_01_create_function(self):
        """Tests a function can be created."""
        mock_function = Function().get_first()
        self.assertEqual(mock_function.name, "Function1")

    def test_02_function_feature_type(self):
        """Tests Function-Featuretype relation."""
        mock_function = Function().get_first()
        self.assertEqual(mock_function.types.name, "feature_name")
