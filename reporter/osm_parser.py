import xml.sax

class OsmParser(xml.sax.ContentHandler):
    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
        self.wayCount = 0
        self.nodeCount = 0
        self.inWay = False
    def startElement(self, name, attrs):
        if name == 'way':
            self.inWay = True
            self.wayCount += 1
        elif name == 'nd' and self.inWay:
            #print("\tattribute type='" + attrs.getValue("type") + "'")
            self.nodeCount += 1
        elif name = 'tag' and self.inWay:
            pass
        else:
            print 'Node not known %s' % name

    def endElement(self, name):
        if name == 'way':
            self.inWay = False


    def characters(self, content):
        pass

def main(sourceFileName):
    myParser = OsmParser()
    source = open(sourceFileName)
    xml.sax.parse(source, myParser)
    print 'Way count %s' % myParser.wayCount
    print 'Node count %s' % myParser.nodeCount

if __name__ == "__main__":
    main("/tmp/reporter.osm")
