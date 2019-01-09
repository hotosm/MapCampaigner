import datetime
import xml.sax
import os
import json
from file_manager import (
    GeojsonFileManager,
    ErrorsFileManager
)


class FeatureCompletenessParser(xml.sax.ContentHandler):

    def __init__(self, required_tags, render_data_path, element_type):
        xml.sax.ContentHandler.__init__(self)
        self.required_tags = required_tags
        self.element_type = element_type

        self.is_element = False
        self.has_tags = False
        self.tags = {}
        self.features_collected = 0 # element has tags
        self.features_completed = 0 # element has no errors
        self.errors_warnings = 0
        self.geojson_file_manager = GeojsonFileManager(
            destination=render_data_path)
        self.errors_file_manager = ErrorsFileManager(
            destination=render_data_path)
        self.error_ids = {
            'node': [],
            'way': [],
            'relation': []

        }
        self.nodes = {}

    def startDocument(self):
        return

    def endDocument(self):
        self.geojson_file_manager.close()
        self.geojson_file_manager.save()
        
        self.errors_file_manager.close()
        self.errors_file_manager.save()

    def startElement(self, name, attrs):
        if name in ['node', 'way']:
            self.build_element(name, attrs)
            self.is_element = True
            self.has_tags = False
            self.element_complete = True

        if self.is_element == True:
            if name == 'tag':
                self.has_tags = True
                self.tags[attrs.getValue('k')] = attrs.getValue('v')
            elif name == 'nd':
                self.has_tags = False

        if self.is_element and self.element['type'] == 'way':
            if name == 'nd':
                ref = attrs.getValue('ref')
                if ref in self.nodes:
                    node = self.nodes[ref]
                    node['used'] = True
                    coordinates = [
                        float(node['lon']),
                        float(node['lat'])
                    ]
                    self.element['nodes'].append(coordinates)

    def endElement(self, name):
        if name == 'node':
            # save the node for later processing
            self.element['processed_data'] = {
                'tags': self.tags
            }

            self.nodes[self.element['id']] = self.element
            self.tags = {}

        if name == 'way':
            self.features_collected += 1
            self.check_element('way')
            self.build_feature('way')
            self.tags = {}

        if name == 'osm':
            # end of file
            for node in self.nodes:
                if self.nodes[node]['used'] == False:
                    self.element = self.nodes[node]
                    self.tags = self.nodes[node]['processed_data']['tags']
                    if len(self.tags) == 0 or self.has_no_required_tags():
                        return
                    self.features_collected += 1
                    self.check_element('node')
                    self.build_feature('node')

    def check_element(self, name):
        self.check_errors_in_tags()
        self.check_warnings_in_tags()
        if self.element_complete:
            self.features_completed += 1
        else:
            self.error_ids[name].append(self.element['id'])

    def has_no_required_tags(self):
        return len(set.intersection(
            set(self.required_tags.keys()), 
            set(self.tags.keys()))) == 0
    
    def build_element(self, name, attrs):
        self.element = {
            'id': attrs.getValue("id"),
            'type': name,
            'timestamp': attrs.getValue("timestamp"),
            'used': False,
            'nodes': [],
            'processed_data': {}
        }
        if name == 'node':
            self.element['lon'] = attrs.getValue("lon")
            self.element['lat'] = attrs.getValue("lat")

    def check_errors_in_tags(self):
        errors = []
        self.errors_to_s = None
        for (key, values) in self.required_tags.items():
            if key not in self.tags.keys():
                error = '{key} not found'.format(key=key)
                errors.append(error)
            else:
                if len(values) > 0 and self.tags[key] not in values:
                    error = '{value} not allowed for value {key}'.format(
                        value=self.tags[key],
                        key=key)
                    errors.append(error)

        if len(errors) > 0:
            self.element_complete = False
            self.errors_to_s = ', '.join(errors)
            self.build_error_warning('error', self.errors_to_s)

        self.completeness_pct = int(100 - \
            (len(errors) / len(self.required_tags) * 100))

    def check_warnings_in_tags(self):
        warnings = []
        self.warnings_to_s = None
        if 'name' in self.tags:
            name = self.tags['name']
            if name.isupper():
                self.element_complete = False
                warning = '{name} is all uppercase'.format(
                    name=name)
                warnings.append(warning)
                
            elif name.islower():
                self.element_complete = False
                warning = '{name} is all lowercase'.format(
                    name=name)
                warnings.append(warning)
            # else:
                # mixed case
        if len(warnings) > 0:
            self.element_complete = False
            self.warnings_to_s = ', '.join(warnings)
            self.build_error_warning('warning', self.warnings_to_s)

    def build_error_warning(self, type, content):
        payload = {
            'status': type,
            'type': self.element['type'],
            'id': self.element['id'],
            'date': self.element['timestamp'],
            'comment': content
        }
        self.errors_file_manager.write(json.dumps(payload))
        self.errors_warnings += 1

    def build_feature(self, osm_type):
        # geo_type = 'Polygon'
        if osm_type == 'node':
            geo_type = 'Point'
            coordinates = [
                float(self.element['lon']), 
                float(self.element['lat'])
            ]
        elif osm_type == 'way':
            if self.element_type == 'Line':
                geo_type = 'LineString'
                coordinates = self.element['nodes']
            elif self.element_type == 'Polygon':
                geo_type = 'Polygon'
                coordinates = [
                    self.element['nodes']
                ]
            else:
                geo_type = 'Polygon'
                coordinates = [
                    self.element['nodes']
                ]

        feature = {
            "type": "Feature",
            "geometry": {
                "type": geo_type,
                "coordinates": coordinates
            },
            "properties": {
                "type": self.element['type'],
                "tags": self.tags,
                "errors": self.errors_to_s,
                "warnings": self.warnings_to_s,
                "completeness_color": self.set_color_completeness(),
                "completeness_pct": '{pct}%'.format(pct=self.completeness_pct)
            },
            "id": self.element['id'],
        }
        self.geojson_file_manager.write(json.dumps(feature))

    def set_color_completeness(self):
        if self.completeness_pct == 100:
            return '#00840d';
        if self.completeness_pct >= 75:
            return '#faff00';
        if self.completeness_pct >= 50:
            return '#ffe500';
        if self.completeness_pct >= 25:
            return '#FD9A08';
        if self.completeness_pct >= 0:
            return '#ff0000';
