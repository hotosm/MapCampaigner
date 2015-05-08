# coding=utf-8

ALL_OVERPASS_QUERY = '(node({SW_lat},{SW_lng},{NE_lat},{NE_lng});<;);out+meta;'

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
    'out+body;')

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
    'out+body;')

OVERPASS_QUERY_MAP = {
    'potential-idp': POTENTIAL_IDP_OVERPASS_QUERY,
    'buildings': BUILDINGS_OVERPASS_QUERY,
    'building-points': BUILDINGS_OVERPASS_QUERY,
    'roads': ROADS_OVERPASS_QUERY,
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

SQL_QUERY_MAP = {
    'potential-idp': POTENTIAL_IDP_SQL_QUERY,
    'buildings': BUILDINGS_SQL_QUERY,
    'building-points': BUILDING_POINTS_SQL_QUERY,
    'roads': ROADS_SQL_QUERY,
}
