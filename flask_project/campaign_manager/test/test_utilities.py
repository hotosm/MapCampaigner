from unittest import TestCase, mock
from campaign_manager.utilities import (
    get_allowed_managers,
    get_types,
    get_survey_json)

class TestUtilities(TestCase):
    def test_get_allowed_managers(self):
        managers = get_allowed_managers()
        self.assertEquals('pierrealixt' in managers, True)

    # def test_get_osm_user(self):
    def test_get_types(self):
        surveys = get_types()
        self.assertEquals(len(surveys), 7)

    def test_get_survey_json(self):
        survey_file = 'buildings'
        survey_json = get_survey_json(survey_file)
        self.assertEquals(survey_json['feature'], 'building')

