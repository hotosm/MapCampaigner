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
            'campaign_uuid': '09a4f0ebb7964189bfc8a5ba8dba2b43',
            'feature': 'amenity=cafe'
        }
        lambda_handler(event, {})


if __name__ == '__main__':
    unittest.main()