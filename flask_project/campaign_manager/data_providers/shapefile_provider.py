__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '29/05/17'

import shapefile
from campaign_manager.data_providers._abstract_data_provider import (
    AbstractDataProvider
)


class ShapefileProvider(AbstractDataProvider):
    """Provider from overpass"""

    def get_data(self, shapefile_file):
        """Get shapefile data.

        :returns: A geojson data from shapefile
        :rtype: dict
        """
        try:
            # read the shapefile
            reader = shapefile.Reader(shapefile_file)
            fields = reader.fields[1:]
            field_names = [field[0] for field in fields]
            buffer = []
            for sr in reader.shapeRecords():
                atr = dict(zip(field_names, sr.record))
                geom = sr.shape.__geo_interface__
                feature = dict(
                    type="Feature",
                    geometry=geom,
                    properties=atr)
                buffer.append(feature)
                if 'date' in feature['properties'] and \
                        feature['properties']['date']:
                    feature['properties']['date'] = \
                        feature['properties']['date'].strftime('%Y-%m-%d')
            return {
                "type": "FeatureCollection",
                "features": buffer
            }
        except shapefile.ShapefileException:
            return {}
