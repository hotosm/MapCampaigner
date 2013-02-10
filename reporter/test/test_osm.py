import os

from reporter.utilities import LOGGER
from reporter.osm import load_osm_document

from reporter.test.logged_unittest import LoggedTestCase


class OsmTestCase(LoggedTestCase):
    """Test the OSM retrieval functions."""

    def test_load_osm_document(self):
        """Check that we can fetch an osm doc and that it caches properly."""
        #
        # NOTE - INTERNET CONNECTION NEEDED FOR THIS TEST
        #
        myUrl = ('http://overpass-api.de/api/interpreter?data='
                 '(node(-34.03112731086964,20.44997155666351,'
                 '-34.029571310785315,20.45501410961151);<;);out+meta;')
        myFilePath = '/tmp/test_load_osm_document.osm'
        if os.path.exists(myFilePath):
            os.remove(myFilePath)
            # We test twice - once to ensure its fetched from the overpass api
        # and once to ensure the cached file is used on second access
        # Note: There is a small chance the second test could fail if it
        # exactly straddles the cache expiry time.
        try:
            myFile = load_osm_document(myFilePath, myUrl)
        except:
            LOGGER.exception('load_osm_document from overpass test failed %s'
                             % myUrl)
            raise
        myString = myFile.read()
        myMessage = 'load_osm_document from overpass content check failed.'
        assert 'Jacoline' in myString, myMessage

        #myFile = load_osm_document(myFilePath, myUrl)
        myFileTime = os.path.getmtime(myFilePath)
        #
        # This one should be cached now....
        #
        load_osm_document(myFilePath, myUrl)
        myFileTime2 = os.path.getmtime(myFilePath)
        myMessage = 'load_osm_document cache test failed.'
        self.assertEqual(myFileTime, myFileTime2, myMessage)
