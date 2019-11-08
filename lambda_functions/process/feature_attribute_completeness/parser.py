import xml.sax
import json
from file_manager import (
    GeojsonFileManager,
    ErrorsFileManager
)


class FeatureCompletenessParser(xml.sax.ContentHandler):

    def __init__(self, required_tags, render_data_path, element_type, type_name):
        xml.sax.ContentHandler.__init__(self)
        self.required_tags = required_tags
        self.element_type = element_type
        self.type_name = type_name
        self.is_element = False
        self.has_tags = False
        self.tags = {}
        self.features_collected = 0  # element has tags
        self.features_completed = 0  # element has no errors
        self.errors_warnings = 0
        self.unused_nodes = {}
        self.geojson_file_manager = GeojsonFileManager(
            destination=render_data_path)
        self.errors_file_manager = ErrorsFileManager(
            destination=render_data_path)
        self.error_ids = {
            'node': [],
            'way': [],
            'relation': []

        }

    def startDocument(self):
        return

    def endDocument(self):
        self.geojson_file_manager.close()
        # self.geojson_file_manager.save()
        self.errors_file_manager.close()
        # self.errors_file_manager.save()

    def startElement(self, name, attrs):
        if name in ['node', 'way']:
            self.build_element(name, attrs)
            self.is_element = True
            self.has_tags = False
            self.element_complete = True

        if self.is_element is True:
            if name == 'tag':
                self.has_tags = True
                self.tags[attrs.getValue('k')] = attrs.getValue('v')
            elif name == 'nd':
                self.has_tags = False

        if self.is_element and self.element['type'] == 'way':
            if name == 'nd':
                ref = attrs.getValue('ref')
                if ref in self.unused_nodes:
                    self.element['nodes'].append(self.unused_nodes[ref])

    def endElement(self, name):
        if name in ['node', 'way']:
            # Remove different elements not related to the element_type.
            if self.has_tags is True:

                if (self.has_no_required_tags() and
                    self.type_name not in self.tags):
                    return
                self.features_collected += 1
                self.check_errors_in_tags()
                self.check_warnings_in_tags()
                if self.element_complete:
                    self.features_completed += 1
                else:
                    self.error_ids[name].append(self.element['id'])

        if name == 'node':
            if self.has_tags is True and self.element_type == 'Point':
                self.build_feature('node')
                self.tags = {}
            elif self.has_tags is False:
                self.unused_nodes[self.element['id']] = [
                    float(self.element['lon']),
                    float(self.element['lat'])
                ]
        if name == 'way' and self.element_type in ['Polygon', 'Line']:
            self.build_feature('way')
            self.tags = {}

    def has_no_required_tags(self):
        return len(set.intersection(
            set(self.required_tags.keys()),
            set(self.tags.keys()))) == 0

    def build_element(self, name, attrs):
        self.element = {
            'id': attrs.getValue("id"),
            'type': name,
            'timestamp': attrs.getValue("timestamp"),
            'nodes': []
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

        self.completeness_pct = int(
            100 - (len(errors) / len(self.required_tags) * 100)
            )

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
            return '#00840d'
        if self.completeness_pct >= 75:
            return '#faff00'
        if self.completeness_pct >= 50:
            return '#ffe500'
        if self.completeness_pct >= 25:
            return '#FD9A08'
        if self.completeness_pct >= 0:
            return '#ff0000'
