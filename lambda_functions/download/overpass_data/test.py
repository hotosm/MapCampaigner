import os
import warnings
import unittest
from lambda_function import (
    lambda_handler
)
from utilities import (
    date_to_dict,
    format_query,
    format_feature_values
)


class TestCase(unittest.TestCase):
    def setUp(self):
        warnings.filterwarnings(
            "ignore",
            category=ResourceWarning,
            message="unclosed.*<ssl.SSLSocket.*>")

    def test_run(self):
        if os.environ.get('ON_TRAVIS', 'false') == 'false':
            event = {
                'campaign_uuid': 'dd7b3627dc6942dc9798ea094f8c680b',
                'type': 'Building'
            }
            lambda_handler(event, {})

    def test_date_to_dict(self):
        start_date = '2018-08-01'
        end_date = '2018-08-31'
        date = date_to_dict(start_date, end_date)
        self.assertEqual(date, {'from': '2018-08-01', 'to': '2018-08-31'})

    def test_format_query_no_value(self):
        formatted_value = format_feature_values([])
        parameters = {
            'polygon': 'polypolygon',
            'print_mode': 'meta',
            'key': 'amenity',
            'value': formatted_value
        }
        query = format_query(parameters)
        self.assertEqual(
            query, '[out:json];(way["amenity"]' +
            '(poly:"polypolygon");node["amenity"](poly:"polypolygon");' +
            'relation["amenity"](poly:"polypolygon"););(._;>;);out meta;')

    def test_format_query_with_value(self):
        formatted_value = format_feature_values(['cafe'])
        parameters = {
            'polygon': 'polypolygon',
            'print_mode': 'meta',
            'key': 'amenity',
            'value': formatted_value
        }
        query = format_query(parameters)
        self.assertEqual(
            query, '[out:json];(way["amenity"~"cafe"](poly:"polypolygon");' +
            'node["amenity"~"cafe"](poly:"polypolygon");relation' +
            '["amenity"~"cafe"](poly:"polypolygon"););(._;>;);out meta;')

    def test_format_query_with_values(self):
        formatted_value = format_feature_values(['cafe', 'coffee'])
        parameters = {
            'polygon': 'polypolygon',
            'print_mode': 'meta',
            'key': 'amenity',
            'value': formatted_value
        }
        query = format_query(parameters)
        self.assertEqual(
            query, '[out:json];(way["amenity"~"cafe|coffee"](poly:"' +
            'polypolygon");node["amenity"~"cafe|coffee"](poly:"polypolygon")' +
            ';relation["amenity"~"cafe|coffee"](poly:"polypolygon"););' +
            '(._;>;);out meta;')


if __name__ == '__main__':
    unittest.main()
