import xml.sax


class ElementParser(xml.sax.ContentHandler):

    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
        self.elements_ids = {
            'node': [],
            'way': [],
            'relation': []
        }

    def startDocument(self):
        return

    def endDocument(self):
        return

    def startElement(self, name, attrs):
        if name == 'node':
            element_id = attrs.getValue('id')
            self.elements_ids['node'].append(str(element_id))
        elif name == 'way':
            element_id = attrs.getValue('id')
            self.elements_ids['way'].append(str(element_id))
        elif name == 'relation':
            element_id = attrs.getValue('id')
            self.elements_ids['relation'].append(str(element_id))

    def endElement(self, name):
        return
