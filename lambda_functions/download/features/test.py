import os
import unittest
from lambda_function import lambda_handler
from utilities import (
  get_unique_features,
)
from test_helper import (
    SELECTED_FUNCTIONS
)


class TestCase(unittest.TestCase):

    def test_run(self):
        if os.environ.get('ON_TRAVIS', 'false') == 'false':
            event = {'campaign_uuid': 'd46b448603254b0caf8c886fe71a4864'}
            lambda_handler(event, {})

    def test_get_unique_features(self):
        unique_features = get_unique_features(SELECTED_FUNCTIONS)
        self.assertEqual(unique_features, {'amenity=cafe', 'shop=supermarket'})

    def test_split_feature_key_values_1(self):
        feature = 'amenity=cafe'
        key, values = split_feature_key_values(feature)
        self.assertEqual(key, 'amenity')
        self.assertEqual(values, ['cafe'])

    def test_split_feature_key_values_2(self):
        feature = 'landuse='
        key, values = split_feature_key_values(feature)
        self.assertEqual(key, 'landuse')
        self.assertEqual(values, None)

    def test_split_feature_key_values_3(self):
        feature = 'amenity=cafe,coffee'
        key, values = split_feature_key_values(feature)
        self.assertEqual(key, 'amenity')
        self.assertEqual(values, ['cafe', 'coffee'])

    def test_filename_1(self):
        feature = 'amenity=cafe'


if __name__ == '__main__':
    unittest.main()
