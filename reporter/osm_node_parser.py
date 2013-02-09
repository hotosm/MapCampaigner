import xml


class OsmNodeParser(xml.sax.ContentHandler):
    """SAX Parser to retrieve nodes from an OSM XML document."""

    def __init__(self, username):
        """Constructor.

        Args:
            username: str - the name of the user for whom nodes should be
                retrieved.

        Returns:
            An OsmNodeParser instance.

        Raises:
            None
        """
        self.username = username
        # A collection of nodes that have been found for a user.
        self.nodes = []

    def startElement(self, name, attributes):
        """Callback for when an element start is encountered.

        Args:
            name: str - the name of the element.
            attributes: dict - collection of key, value pairs representing
                the attributes of the element.
        Returns:
            None
        Raises:
            None
        """
        if name == 'node':
            if attributes.getValue('user') == self.username:
                self.nodes.append((float(attributes.getValue('lat')),
                                   float(attributes.getValue('lon'))))
