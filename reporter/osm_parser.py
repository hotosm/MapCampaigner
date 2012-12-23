import xml.sax

class OsmParser(xml.sax.ContentHandler):
    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
        self.wayCount = 0
        self.nodeCount = 0
        self.inWay = False
        self.user = None
        self.building = False
        self.wayCountDict = {}
        self.nodeCountDict = {}

    def startElement(self, name, attrs):
        if name == 'way':
            self.inWay = True
            self.wayCount += 1
            self.user = attrs.getValue('user')
        elif name == 'nd' and self.inWay:
            self.nodeCount += 1
        elif name == 'tag' and self.inWay:
            if attrs.getValue('k') == 'building':
                self.building = True
        else:
            pass
            #print 'Node not known %s' % name

    def endElement(self, name):
        if name == 'way':
            if self.building:
                # Its a building so update our building and node counts
                if self.user in self.wayCountDict:
                    myValue = self.wayCountDict[self.user]
                    self.wayCountDict[self.user] = myValue + 1
                    myValue = self.nodeCountDict[self.user]
                    self.nodeCountDict[self.user] = myValue + self.nodeCount
                else:
                    self.wayCountDict[self.user] = 1
                    self.nodeCountDict[self.user] = self.nodeCount

            self.inWay = False
            self.user = None
            self.building = False
            self.nodeCount = 0
            self.wayCount = 0


    def characters(self, content):
        pass

