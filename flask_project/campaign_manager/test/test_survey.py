from unittest import TestCase
from campaign_manager.models.survey import Survey


class TestSurvey(TestCase):

    def test_init_survey_buildings(self):
        """
        It should initialize a 'buildings' Survey object.
        """
        survey = Survey('buildings')
        self.assertEqual(survey.data['tags']['building'], ['yes'])

    def test_all(self):
        """
        It should return all the surveys.
        """
        surveys = Survey.all()
        self.assertEqual(len(surveys), 7)
        self.assertEqual('buildings' in surveys, True)

    def test_unknown_survey(self):
        """
        It should return an empty array.
        """
        survey = Survey.find_by_name('unknown')
        self.assertEqual(survey.data, [])

    def test_survey_features(self):
        """
        It should return survey's features.
        """
        survey = Survey.find_by_name('buildings')
        self.assertEqual(survey.feature, 'building')
