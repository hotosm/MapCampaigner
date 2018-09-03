import os
import unittest
import warnings
from lambda_function import lambda_handler


class TestCase(unittest.TestCase):
    def setUp(self):
        warnings.filterwarnings(
            "ignore",
            category=ResourceWarning,
            message="unclosed.*<ssl.SSLSocket.*>")

    def test_run(self):
        if os.environ.get('ON_TRAVIS', 'false') == 'false':
            event = {
                'campaign_uuid': '76674eefa4524a6fbc20e147fe01f1fd',
                'feature': 'building=yes',
                'date': {
                    'from': '2018-01-01',
                    'to': '2019-12-31'
                }
            }
            lambda_handler(event, {})


if __name__ == '__main__':
    unittest.main()
