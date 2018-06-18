import os
from unittest import TestCase
from campaign_manager.models.models import *
from sqlalchemy.orm import sessionmaker


def db_setUp():
    db_location = os.environ['TESTDATABASE_URL']
    engine = create_engine(db_location, echo=True)
    return engine


# Destroy the mock test Database
def db_destroy(engine):
    for tbl in reversed(meta.sorted_tables):
        engine.execute(tbl.delete())


# Create a session for the Database
def create_session(engine):
    Session = sessionmaker(bind=engine)
    Session.configure(bind=engine)
    session = Session()
    return session


engine_test = db_setUp()
Base.metadata.create_all(engine_test)
session = create_session(engine_test)


"""Tests for Table: User"""


def get_mock_user(username, email):
    mock_user = User(
        osm_user_id=username,
        email=email
        )
    session.add(mock_user)
    session.commit()
    return mock_user


def delete_mock_user(user_object):
    session.delete(user_object)
    session.commit()


class TestUser(TestCase):

    def test_01_user_name(self):
        mock_user = get_mock_user(
            "user",
            "email@gmail.com"
            )
        self.assertEqual(mock_user.osm_user_id, "user")

    def test_02_update_user_email(self):
        mock_user = session.query(User).first()
        mock_user.email = "new_email@gmail.com"
        session.commit()
        mock_user = session.query(User).first()
        self.assertEqual(mock_user.email, "new_email@gmail.com")

    def test_03_max_osm_id_length(self):
        mock_user = session.query(User).first()
        osm_user_id_len_check = (len(mock_user.osm_user_id) < 20)
        self.assertTrue(osm_user_id_len_check)

    def test_04_delete_user(self):
        mock_user = session.query(User).first()
        delete_mock_user(mock_user)
        test_mock_user = session.query(User).first()
        self.assertFalse(test_mock_user)


"""Tests for Table: Campaign"""


def get_mock_campaign(
        creator_id,
        name,
        description,
        start_date,
        end_date,
        create_on):
    mock_campaign = Campaign(
        creator_id=creator_id,
        name=name,
        description=description,
        start_date=start_date,
        end_date=end_date,
        create_on=create_on
        )
    session.add(mock_campaign)
    session.commit()
    return mock_campaign


def delete_mock_campaing(campaign_object):
    session.delete(campaign_object)
    session.commit()


class TestCampaign(TestCase):

    def test_01_campaign_name(self):
        import datetime
        mock_user = get_mock_user(
            "user",
            "email@gmail.com"
            )
        mock_campaign = get_mock_campaign(
            mock_user.id,
            "campaign",
            "campaign_description",
            datetime.date(2018, 1, 1),
            datetime.date(2018, 1, 1),
            datetime.datetime.now()
            )
        self.assertEqual(mock_campaign.name, "campaign")

    def test_02_campaign_creator(self):
        mock_campaign = session.query(Campaign).first()
        self.assertEqual(mock_campaign.creator.osm_user_id, "user")

    def test_03_update_campaign(self):
        mock_campaign = session.query(Campaign).first()
        mock_campaign.name = "new_campaign_name"
        session.commit()
        mock_campaign = session.query(Campaign).first()
        self.assertEqual(mock_campaign.name, "new_campaign_name")

    def test_04_geom_campaign(self):
        import ast
        from geoalchemy2.shape import from_shape
        from shapely.geometry import asShape
        geom = {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [
                                -22.7271314710379,
                                23.9871672761574
                            ],
                            [
                                -22.7271314710379,
                                23.9879122455024
                            ],
                            [
                                -22.7264448255301,
                                23.9879122455024
                            ],
                            [
                                -22.7264448255301,
                                23.9871672761574
                            ],
                            [
                                -22.7271314710379,
                                23.9871672761574
                            ]
                        ]
                    ]
                }
        geom_obj = from_shape(
            asShape(geom),
            srid=4326
            )
        mock_campaign = session.query(Campaign).first()
        mock_taskBoundary = TaskBoundary(
            coordinates=geom_obj,
            name="name",
            status="status",
            type_boundary="type_boundary",
            campaign_id=mock_campaign.id
            )
        session.commit()
        self.assertEqual(mock_taskBoundary.coordinates, geom_obj)

    def test_05_default_feild_condition(self):
        mock_campaign = session.query(Campaign).first()
        self.assertFalse(mock_campaign.link_to_OpenMapKit)

    def test_06_delete_campaign(self):
        mock_campaign = session.query(Campaign).first()
        mock_user = session.query(User).first()
        delete_mock_campaing(mock_campaign)
        delete_mock_user(mock_user)
        test_mock_campaign = session.query(Campaign).first()
        self.assertFalse(test_mock_campaign)


"""Tests for Table: FeatureType"""


def get_mock_attributes(feature_type_object):
    attribute1 = Attribute(attribute_name="attribute1")
    attribute2 = Attribute(attribute_name="attribute2")
    session.add(attribute1)
    session.add(attribute2)
    session.commit()
    feature_type_object.attributes.append(attribute1)
    feature_type_object.attributes.append(attribute2)
    session.commit()


def get_mock_featureType(feature, name):
    mock_feature_type = FeatureType(
        feature=feature,
        name=name
        )
    session.add(mock_feature_type)
    session.commit()
    get_mock_attributes(mock_feature_type)
    return mock_feature_type


def delete_mock_featureType(feature_type_object):
    session.delete(feature_type_object)
    session.commit()


class TestFeatureType(TestCase):

    def test_01_featuretype_length(self):
        mock_feature_type = get_mock_featureType(
            "feature",
            "feature_name"
            )
        check_len = (len(mock_feature_type.name) < 20)
        self.assertTrue(check_len)

    def test_02_default_field(self):
        mock_feature_type = session.query(FeatureType).first()
        self.assertFalse(mock_feature_type.is_template)

    def test_03_attributes(self):
        mock_feature_type = session.query(FeatureType).first()
        attributes_obj = mock_feature_type.attributes
        attributes = [x.attribute_name for x in attributes_obj]
        attribute_check = (attributes == ["attribute1", "attribute2"])
        self.assertTrue(attribute_check)

    def test_04_delete_feature_type(self):
        mock_feature_type = session.query(FeatureType).first()
        delete_mock_featureType(mock_feature_type)
        mock_feature_type = session.query(FeatureType).first()
        self.assertFalse(mock_feature_type)


"""Tests for Table: FeatureTemplate"""


def get_feature_template(featureType):
    template = FeatureTemplate(
        name="Template",
        description="Template_description",
        featureType_id=featureType.id
        )
    session.add(template)
    session.commit()


def get_mock_template_featureType(name, feature, is_template):
    featureType = FeatureType(
        name=name,
        feature=feature,
        is_template=is_template
        )
    session.add(featureType)
    session.commit()
    get_mock_attributes(featureType)
    return featureType


def delete_mock_template_featureType(featureType):
    session.delete(featureType)
    session.commit()


class TestFeatureTemplate(TestCase):

    def test_01_is_template(self):
        featureType = get_mock_template_featureType(
            "feature",
            "feature_nane",
            True
            )
        self.assertTrue(featureType.is_template)

    def test_02_feature_template_name(self):
        mock_feature = session.query(FeatureType).first()
        get_feature_template(mock_feature)
        template = session.query(FeatureTemplate).first()
        self.assertEqual(template.name, "Template")

    def test_03_delete_template(self):
        template = session.query(FeatureTemplate).first()
        featureType = session.query(FeatureType).first()
        delete_mock_template_featureType(template)
        delete_mock_template_featureType(featureType)
        template = session.query(FeatureTemplate).first()
        self.assertFalse(template)


"""Tests for Table: TaskBoundary"""


def get_mock_task_boundary(
        coordinates,
        name,
        status,
        type_boundary,
        campaign_id):
    mock_taskBoundary = TaskBoundary(
        coordinates=coordinates,
        name=name,
        status=status,
        type_boundary=type_boundary,
        campaign_id=campaign_id
        )
    session.add(mock_taskBoundary)
    session.commit()


def delete_mock_task_boundary(task_boundary_obj):
    session.delete(task_boundary_obj)
    session.commit()


class TestTaskBoundary(TestCase):
    def test_01_create_task_boundary(self):
        import ast
        from geoalchemy2.shape import from_shape
        from shapely.geometry import asShape
        import datetime
        geom = {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [
                                -22.7271314710379,
                                23.9871672761574
                            ],
                            [
                                -22.7271314710379,
                                23.9879122455024
                            ],
                            [
                                -22.7264448255301,
                                23.9879122455024
                            ],
                            [
                                -22.7264448255301,
                                23.9871672761574
                            ],
                            [
                                -22.7271314710379,
                                23.9871672761574
                            ]
                        ]
                    ]
                }
        geom_obj = from_shape(asShape(geom), srid=4326)
        mock_user = get_mock_user(
            "user",
            "email@gmail.com"
            )
        mock_campaign = get_mock_campaign(
            mock_user.id,
            "campaign",
            "campaign_description",
            datetime.date(2018, 1, 1),
            datetime.date(2018, 1, 1),
            datetime.datetime.now()
            )
        mock_task_boundary = get_mock_task_boundary(
            geom_obj,
            "Area1",
            "inactive",
            "Feature",
            mock_campaign.id
            )
        mock_task_boundary = session.query(
            TaskBoundary.coordinates.ST_AsGeoJSON()
            ).first()
        geom_check = (geom == ast.literal_eval(mock_task_boundary[0]))
        self.assertTrue(geom_check)

    def test_02_task_boundary_geom_type(self):
        import ast
        mock_campaign = session.query(Campaign).first()
        mock_geom_obj = session.query(
            TaskBoundary.coordinates.ST_AsGeoJSON()).filter(
            TaskBoundary.campaign_id == mock_campaign.id
            ).first()
        mock_geom_obj = ast.literal_eval(mock_geom_obj[0])
        self.assertEqual(mock_geom_obj['type'], "Polygon")

    def test_03_task_boundary_campaign_relation(self):
        mock_task_boundary = session.query(TaskBoundary).first()
        mock_user = session.query(User).first()
        mock_campaign = session.query(Campaign).first()
        mock_task_boundary.campaign_id = mock_campaign.id
        session.commit()
        self.assertEqual(mock_task_boundary.campaign.name, "campaign")

    def test_04_delete_task_boundary(self):
        mock_campaign = session.query(Campaign).first()
        mock_user = session.query(User).first()
        mock_task_boundary = session.query(TaskBoundary).first()
        delete_mock_task_boundary(mock_task_boundary)
        delete_mock_campaing(mock_campaign)
        delete_mock_user(mock_user)
        mock_task_boundary = session.query(TaskBoundary).first()
        self.assertFalse(mock_task_boundary)


"""Tests for Table: Team"""


def create_mock_team(name, boundary_id):
    mock_team = Team(
        name=name,
        boundary_id=boundary_id
        )
    session.add(mock_team)
    session.commit()
    return mock_team


def delete_mock_team(team_obj):
    session.delete(team_obj)
    session.commit()


class TestTeam(TestCase):

    def test_01_create_team(self):
        import ast
        from geoalchemy2.shape import from_shape
        from shapely.geometry import asShape
        import datetime
        geom = {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [
                                -22.7271314710379,
                                23.9871672761574
                            ],
                            [
                                -22.7271314710379,
                                23.9879122455024
                            ],
                            [
                                -22.7264448255301,
                                23.9879122455024
                            ],
                            [
                                -22.7264448255301,
                                23.9871672761574
                            ],
                            [
                                -22.7271314710379,
                                23.9871672761574
                            ]
                        ]
                    ]
                }
        geom_obj = from_shape(
            asShape(geom),
            srid=4326
            )
        mock_user = get_mock_user(
            "user",
            "email@gmail.com"
            )
        mock_campaign = get_mock_campaign(
            mock_user.id,
            "campaign",
            "campaign_description",
            datetime.date(2018, 1, 1),
            datetime.date(2018, 1, 1),
            datetime.datetime.now()
            )
        mock_task_boundary = get_mock_task_boundary(
            geom_obj,
            "Area1",
            "inactive",
            "Feature",
            mock_campaign.id
            )
        mock_task_boundary = session.query(TaskBoundary).first()
        mock_team = create_mock_team(
            "Team7",
            mock_task_boundary.id
            )
        self.assertEqual(mock_team.name, "Team7")

    def test_02_update_team_name(self):
        mock_team = session.query(Team).first()
        mock_team.name = "new_team7"
        session.commit()
        mock_team = session.query(Team).first()
        self.assertEqual(mock_team.name, "new_team7")

    def test_03_delete_team(self):
        mock_campaign = session.query(Campaign).first()
        mock_user = session.query(User).first()
        mock_team = session.query(Team).first()
        mock_task_boundary = session.query(TaskBoundary).first()
        delete_mock_team(mock_team)
        delete_mock_task_boundary(mock_task_boundary)
        delete_mock_user(mock_campaign)
        delete_mock_user(mock_user)
        mock_team = session.query(Team).first()
        self.assertFalse(mock_team)


"""Tests for Table: Function"""


def get_mock_function(name, feature, type_id):
    mock_function = Function(
        name=name,
        feature=feature,
        type_id=type_id
        )
    session.add(mock_function)
    session.commit()


def delete_mock_function(function_obj):
    session.delete(function_obj)
    session.commit()


class TestFunction(TestCase):

    def test_01_create_function(self):
        featureType = get_mock_template_featureType(
            "feature",
            "feature_nane",
            True
            )
        mock_function = get_mock_function(
            "Function1",
            "data_collection",
            featureType.id
            )
        mock_function = session.query(Function).first()
        self.assertEqual(mock_function.name, "Function1")

    def test_02_function_feature_type(self):
        mock_feature_type = get_mock_featureType(
            "feature",
            "feature_name"
            )
        mock_function = session.query(Function).first()
        mock_function.type_id = mock_feature_type.id
        session.commit()
        mock_function = session.query(Function).first()
        self.assertEqual(mock_function.types.name, "feature_name")

    def test_03_delete_function(self):
        mock_feature_type = session.query(FeatureType).first()
        delete_mock_featureType(mock_feature_type)
        mock_function = session.query(Function).first()
        delete_mock_function(mock_function)
        mock_function = session.query(Function).first()
        self.assertFalse(mock_function)
