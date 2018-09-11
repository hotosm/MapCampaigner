import unittest
import warnings
import os
import json
from lambda_function import (
    lambda_handler
)
from utilities import (    
    fetch_required_tags,
)
from parser import GeojsonFileManager


class TestFileManager(unittest.TestCase):
    def setUp(self):
        for i in range(1, 4):
            file = '/tmp/geojson_{i}.json'.format(i=i)
            if os.path.isfile(file):
                os.remove(file)
            file = '/tmp/errors{i}.json'.format(i=i)
            if os.path.isfile(file):
                os.remove(file)

    def test_create_file(self):
        geojson_file_manager = GeojsonFileManager()
        geojson_file_manager.close()
        self.assertEqual(os.path.isfile('/tmp/geojson_1.json'), True)

    def test_write_large_data(self):
        """
        It should create 3 geojson files.
        """
        
        geojson = json.dumps({"type": "Feature", "geometry": {"type": "Point", "coordinates": ["-9.1334205", "38.7135886"]}, "properties": {"popup": "self.build_popup()"}, "id": "296224622", "completeness_color": "#ff0000", "completeness_pct": "0%"})
        geojson_file_manager = GeojsonFileManager()
        for _ in range(50000):
            geojson_file_manager.write(geojson)
        geojson_file_manager.close()

        self.assertEqual(os.path.isfile('/tmp/geojson_1.json'), True)
        self.assertEqual(os.path.isfile('/tmp/geojson_2.json'), True)
        self.assertEqual(os.path.isfile('/tmp/geojson_3.json'), True)

    def test_write_geojson(self):
        geojson = json.dumps({"type": "Feature", "geometry": {"type": "Point", "coordinates": ["-9.1334205", "38.7135886"]}, "properties": {"popup": "self.build_popup()"}, "id": "296224622", "completeness_color": "#ff0000", "completeness_pct": "0%"})
        geojson_file_manager = GeojsonFileManager()
        for _ in range(50):
            geojson_file_manager.write(geojson)
        geojson_file_manager.close()
        try:
            with open('/tmp/geojson_1.json', 'r') as f:
                geojson = json.load(f)
                json_valid = True
        except:
            json_valid = False

        self.assertEqual(json_valid, True)

    def test_write_large_errors(self):
        payload = {
            'status': 'error',
            'name': 'https://www.openstreetmap.org/error/13000',
            'date': '1000',
            'comment': 'not found'
        }
        error = json.dumps(payload)


class TestCase(unittest.TestCase):
    def setUp(self):
        warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed.*<ssl.SSLSocket.*>")   
  
    def test_run(self):
        event = {
           'campaign_uuid': '08c11d5fca144960bb909f02982a06f9', 
           'feature': 'amenity'
        }
        lambda_handler(event, {})

    def test_fetch_required_tags(self):
        feature = 'amenity=cafe'
        functions = {
            "function-1": {
            "function": "FeatureAttributeCompleteness", 
            "feature": "amenity=cafe", 
            "attributes": {"amenity": ["cafe"], "name": [], "cuisine": [], "operator": [], "opening_hours": []}, 
            "type": "cafe"}, 
        "function-2": {
            "function": "CountFeature", "feature": "amenity=cafe", 
            "attributes": {"amenity": ["cafe"], "name": [], "cuisine": [], "operator": [], "opening_hours": []},
            "type": "cafe"}, 
        "function-3": {
            "function": "MapperEngagement", "feature": "amenity=cafe", 
            "attributes": {"amenity": ["cafe"], "name": [], "cuisine": [], "operator": [], "opening_hours": []}, 
            "type": "cafe"}, 
        "function-4": {
            "function": "FeatureAttributeCompleteness", "feature": "shop=supermarket", 
            "attributes": {"shop": ["supermarket"], "name": []}, 
            "type": "supermarket"}, 
        "function-5": {
            "function": "CountFeature", "feature": "shop=supermarket", 
            "attributes": {"shop": ["supermarket"], "name": []},
            "type": "supermarket"}, 
        "function-6": {
            "function": "MapperEngagement", 
            "feature": "shop=supermarket", 
            "attributes": {"shop": ["supermarket"], "name": []}, 
            "type": "supermarket"}
        }
        required_tags = fetch_required_tags(feature, functions)
        self.assertEqual(required_tags, {"amenity": ["cafe"], "name": [], "cuisine": [], "operator": [], "opening_hours": []})


if __name__ == '__main__':
    unittest.main()
