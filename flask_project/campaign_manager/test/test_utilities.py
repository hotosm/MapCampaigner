from unittest import TestCase
from campaign_manager.utilities import (
    get_allowed_managers,
    get_types,
    get_survey_json)
import os


class TestUtilities(TestCase):
    def test_get_allowed_managers(self):
        managers = get_allowed_managers()
        self.assertEquals('pierrealixt' in managers, True)

    def test_get_types(self):
        surveys = get_types()
        self.assertEquals(len(surveys), 7)

    def test_get_survey_json(self):
        surveyPath = os.path.join(
            os.path.dirname(__file__),
            '../feature_templates',
            'buildings.yml'
        )
        survey_json = get_survey_json(surveyPath)
        self.assertEquals(survey_json['feature'], 'building=yes')
