import unittest
import warnings
from lambda_function import (
    lambda_handler
)


class TestCase(unittest.TestCase):
    def setUp(self):
        warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed.*<ssl.SSLSocket.*>")   

    def test_run(self):
        event = {
           'campaign_uuid': '3a2c5987a9c248cb93537e9c3a37c87c', 
           'feature': 'amenity'
        }
        lambda_handler(event, {})

if __name__ == '__main__':
    unittest.main()