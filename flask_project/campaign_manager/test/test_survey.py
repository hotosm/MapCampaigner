from unittest import TestCase, mock
from campaign_manager.models.survey import Survey

class TestSurvey(TestCase):

    def test_init_survey_buildings(self):
        """
        It should initialize a 'buildings' Survey object.
        """
        survey = Survey('buildings')
        self.assertEquals(survey.data['tags']['building'], ['yes'])


    def test_all(self):
        """
        It should return all the surveys.
        """
        surveys = Survey.all()
        self.assertEqual(len(surveys), 7)
        self.assertEqual(surveys[0], 'buildings')


    def test_unknown_survey(self):
        """
        It should return an empty array.
        """
        unknown_survey = Survey.find_by_name('unknown')
        self.assertEquals(unknown_survey.data, [])


    def test_survey_features(self):
        """
        It should return survey's features.
        """
        survey = Survey.find_by_name('buildings')
        print(survey.data)
        self.assertEquals(survey.features, [])
