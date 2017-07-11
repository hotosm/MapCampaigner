# coding=utf-8
import unittest
import os
from campaign_manager.utilities import module_path, get_survey_json


class SurveyTestCase(unittest.TestCase):
    """Test function for converting survey to readable json."""

    def setUp(self):
        """Constructor."""
        self.survey_folder = os.path.join(
            module_path(),
            'campaigns_data',
            'surveys'
        )

    def tearDown(self):
        """Destructor."""
        pass

    def test_all_file_test(self):
        for filename in os.listdir(self.survey_folder):
            if '.gitkeep' in filename:
                continue

            # check the json for each file
            survey_path = os.path.join(
                self.survey_folder,
                filename
            )
            survey = get_survey_json(survey_path)
            self.assertIsNotNone(survey['feature'])
