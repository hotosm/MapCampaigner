import datetime
import xml.sax
import os
import json


class CountFeatureParser(xml.sax.ContentHandler):

    def __init__(self, feature):
        xml.sax.ContentHandler.__init__(self)
        features = feature.split('=')
        if len(features) > 0:
            self.feature_key = features[0]
        self.count = {}

    def startDocument(self):
        return

    def endDocument(self):
        return

    def startElement(self, name, attrs):
        if name == 'tag':
            key = attrs.getValue('k')
            if key == self.feature_key:
                value = attrs.getValue('v')
                if value in self.count:
                    self.count[value] += 1
                else:
                    self.count[value] = 0


    def endElement(self, name):
        return

