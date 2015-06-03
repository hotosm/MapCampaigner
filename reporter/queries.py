# coding=utf-8

ALL_OVERPASS_QUERY = '(node({SW_lat},{SW_lng},{NE_lat},{NE_lng});<;);out meta;'

POTENTIAL_IDP_OVERPASS_QUERY = (
    '('
    # Amenity school
    'node["amenity"="school"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["amenity"="school"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'relation["amenity"="school"]'

    # Amenity hospital
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'node["amenity"="hospital"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["amenity"="hospital"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'relation["amenity"="hospital"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'

    # Amenity university
    'node["amenity"="university"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["amenity"="university"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'relation["amenity"="university"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'

    # Amenity college
    'node["amenity"="college"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["amenity"="college"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'relation["amenity"="college"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'

    # Amenity place of worship
    'node["amenity"="place_of_worship"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["amenity"="place_of_worship"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'relation["amenity"="place_of_worship"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'

    # Building public
    'node["building"="public"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["building"="public"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'relation["building"="public"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'

    # Leisure sport centre
    'node["leisure"="sport_centre"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["leisure"="sport_centre"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'relation["leisure"="sport_centre"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'

    ');'
    '(._;>;);'
    'out body;'
)

BUILDINGS_OVERPASS_QUERY = (
    '('
    'node["building"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["building"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'relation["building"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out body;')

ROADS_OVERPASS_QUERY = (
    '('
    'node["highway"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["highway"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'relation["highway"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out body;')

BOUNDARY_1_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="1"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out body;')

BOUNDARY_2_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="2"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out body;')

BOUNDARY_3_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="3"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out body;')

BOUNDARY_4_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="4"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out body;')

BOUNDARY_5_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="5"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out body;')

BOUNDARY_6_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="6"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out body;')

BOUNDARY_7_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="7"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out body;')

BOUNDARY_8_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="8"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out body;')

BOUNDARY_9_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="9"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out body;')

BOUNDARY_10_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="10"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out body;')

BOUNDARY_11_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="11"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out body;')

OVERPASS_QUERY_MAP = {
    'potential-idp': POTENTIAL_IDP_OVERPASS_QUERY,
    'buildings': BUILDINGS_OVERPASS_QUERY,
    'building-points': BUILDINGS_OVERPASS_QUERY,
    'roads': ROADS_OVERPASS_QUERY,
    'boundary-1': BOUNDARY_1_OVERPASS_QUERY,
    'boundary-2': BOUNDARY_2_OVERPASS_QUERY,
    'boundary-3': BOUNDARY_3_OVERPASS_QUERY,
    'boundary-4': BOUNDARY_4_OVERPASS_QUERY,
    'boundary-5': BOUNDARY_5_OVERPASS_QUERY,
    'boundary-6': BOUNDARY_6_OVERPASS_QUERY,
    'boundary-7': BOUNDARY_7_OVERPASS_QUERY,
    'boundary-8': BOUNDARY_8_OVERPASS_QUERY,
    'boundary-9': BOUNDARY_9_OVERPASS_QUERY,
    'boundary-10': BOUNDARY_10_OVERPASS_QUERY,
    'boundary-11': BOUNDARY_11_OVERPASS_QUERY,
    'all': ALL_OVERPASS_QUERY
}

# Used to extract the features as a shapefile from pg
# We don't store in an sql file as the sql needs to be escaped
# as it is passed as an inline command line option to pgsql2shp

POTENTIAL_IDP_SQL_QUERY = (
    '"SELECT ST_Transform(way, 4326) AS the_geom, '
    'type, '
    'building, '
    '\\"capacity:persons\\" AS capacity, '
    '\\"addr:full\\" AS full_address, '
    '\\"addr:housename\\", '
    '\\"addr:housenumber\\", '
    '\\"addr:interpolation\\", '
    '\\"building:use\\" AS use, '
    '\\"building:structure\\" AS structure, '
    '\\"building:walls\\" AS wall_type, '
    '\\"building:roof\\" AS roof_type, '
    '\\"building:levels\\" AS levels, '
    'access, '
    '\\"access:roof\\" AS roof_access, '
    'amenity, '
    'leisure, '
    'religion, '
    'denomination, '
    'sport '
    'FROM idp;"')

ROADS_SQL_QUERY = (
    '"SELECT st_transform(way, 4326) AS the_geom, '
    '"name", '
    'highway as osm_type,'
    'type '
    'FROM planet_osm_line '
    'WHERE highway != \'no\';"')

BUILDING_POINTS_SQL_QUERY = (
    '"SELECT st_transform(st_pointonsurface(way), 4326) AS the_geom, '
    'building AS building, '
    'type, '
    'cast(st_area(st_transform(way, 3857)) as integer) as area_meters, '
    '\\"building:structure\\" AS structure, '
    '\\"building:walls\\" AS wall_type, '
    '\\"building:roof\\" AS roof_type, '
    '\\"building:levels\\" AS levels, '
    'admin_level AS admin, '
    '\\"access:roof\\" AS roof_access, '
    '\\"capacity:persons\\" AS capacity, '
    'religion, '
    '\\"type:id\\" AS osm_type , '
    '\\"addr:full\\" AS full_address, '
    'name, '
    'amenity, '
    'leisure, '
    '\\"building:use\\" AS use, '
    'office '
    'FROM planet_osm_polygon '
    'WHERE building != \'no\';"')

BUILDINGS_SQL_QUERY = (
    '"SELECT st_transform(way, 4326) AS the_geom, '
    'building AS building, '
    'type, '
    '\\"building:structure\\" AS structure, '
    '\\"building:walls\\" AS wall_type, '
    '\\"building:roof\\" AS roof_type, '
    '\\"building:levels\\" AS levels, '
    'admin_level AS admin, '
    '\\"access:roof\\" AS roof_access, '
    '\\"capacity:persons\\" AS capacity, '
    'religion, '
    '\\"type:id\\" AS osm_type , '
    '\\"addr:full\\" AS full_address, '
    'name, '
    'amenity, '
    'leisure, '
    '\\"building:use\\" AS use, '
    'office '
    'FROM planet_osm_polygon '
    'WHERE building != \'no\';"')

BOUNDARY_SQL_QUERY = (
    '"SELECT ST_Transform(way, 4326) AS the_geom, '
    'name, '
    'population, '
    'ref, '
    'admin_level AS level '
    'FROM planet_osm_polygon"')

SQL_QUERY_MAP = {
    'potential-idp': POTENTIAL_IDP_SQL_QUERY,
    'buildings': BUILDINGS_SQL_QUERY,
    'building-points': BUILDING_POINTS_SQL_QUERY,
    'roads': ROADS_SQL_QUERY,
    'boundary-1': BOUNDARY_SQL_QUERY,
    'boundary-2': BOUNDARY_SQL_QUERY,
    'boundary-3': BOUNDARY_SQL_QUERY,
    'boundary-4': BOUNDARY_SQL_QUERY,
    'boundary-5': BOUNDARY_SQL_QUERY,
    'boundary-6': BOUNDARY_SQL_QUERY,
    'boundary-7': BOUNDARY_SQL_QUERY,
    'boundary-8': BOUNDARY_SQL_QUERY,
    'boundary-9': BOUNDARY_SQL_QUERY,
    'boundary-10': BOUNDARY_SQL_QUERY,
    'boundary-11': BOUNDARY_SQL_QUERY,
}

# The name of the resource folder to use for the feature.
RESOURCES_MAP = {
    'buildings': 'buildings',
    'building-points': 'building-points',
    'roads': 'roads',
    'potential-idp': 'potential-idp',
    'boundary-1': 'boundary',
    'boundary-2': 'boundary',
    'boundary-3': 'boundary',
    'boundary-4': 'boundary',
    'boundary-5': 'boundary',
    'boundary-6': 'boundary',
    'boundary-7': 'boundary',
    'boundary-8': 'boundary',
    'boundary-9': 'boundary',
    'boundary-10': 'boundary',
    'boundary-11': 'boundary'
}
