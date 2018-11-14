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
           'campaign_uuid': '6f35021df8864397903a60e0d5853920', 
           'type': 'SHOP_AS_POLYGON'
        }
        lambda_handler(event, {})


if __name__ == '__main__':
    unittest.main()