# coding=utf-8

FEATURES = [
    'potential-idp',
    'evacuation-centers',
    'buildings',
    'building-points',
    'flood-prone',
    'roads',
    'boundary-1',
    'boundary-2',
    'boundary-3',
    'boundary-4',
    'boundary-5',
    'boundary-6',
    'boundary-7',
    'boundary-8',
    'boundary-9',
    'boundary-10',
    'boundary-11',
]

TAG_MAPPING = {
    'highway': 'roads',
    'building': 'buildings',
    'evacuation_center': 'evacuation-centers',
    'flood_prone': 'flood-prone'
}

TAG_MAPPING_REVERSE = {
    'roads': 'highway',
    'buildings': 'building',
    'evacuation-centers': 'evacuation_center',
    'flood-prone': 'flood_prone'
}

POTENTIAL_IDP_OVERPASS_QUERY = (
    '('
    # Amenity school
    'node["amenity"="school"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["amenity"="school"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'relation["amenity"="school"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'

    # Amenity hospital
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
    'out {print_mode};'
)

POTENTIAL_IDP_OVERPASS_QUERY_POLYGON = (
    '('
    # Amenity school
    'node["amenity"="school"]'
    '(poly:"{polygon}");'
    'way["amenity"="school"]'
    '(poly:"{polygon}");'
    'relation["amenity"="school"]'
    '(poly:"{polygon}");'

    # Amenity hospital
    'node["amenity"="hospital"]'
    '(poly:"{polygon}");'
    'way["amenity"="hospital"]'
    '(poly:"{polygon}");'
    'relation["amenity"="hospital"]'
    '(poly:"{polygon}");'

    # Amenity university
    'node["amenity"="university"]'
    '(poly:"{polygon}");'
    'way["amenity"="university"]'
    '(poly:"{polygon}");'
    'relation["amenity"="university"]'
    '(poly:"{polygon}");'

    # Amenity college
    'node["amenity"="college"]'
    '(poly:"{polygon}");'
    'way["amenity"="college"]'
    '(poly:"{polygon}");'
    'relation["amenity"="college"]'
    '(poly:"{polygon}");'

    # Amenity place of worship
    'node["amenity"="place_of_worship"]'
    '(poly:"{polygon}");'
    'way["amenity"="place_of_worship"]'
    '(poly:"{polygon}");'
    'relation["amenity"="place_of_worship"]'
    '(poly:"{polygon}");'

    # Building public
    'node["building"="public"]'
    '(poly:"{polygon}");'
    'way["building"="public"]'
    '(poly:"{polygon}");'
    'relation["building"="public"]'
    '(poly:"{polygon}");'

    # Leisure sport centre
    'node["leisure"="sport_centre"]'
    '(poly:"{polygon}");'
    'way["leisure"="sport_centre"]'
    '(poly:"{polygon}");'
    'relation["leisure"="sport_centre"]'
    '(poly:"{polygon}");'

    ');'
    '(._;>;);'
    'out {print_mode};'
)

EVACUATION_CENTERS_OVERPASS_QUERY = (
    '('
    'node["evacuation_center"="yes"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["evacuation_center"="yes"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'relation["evacuation_center"="yes"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out {print_mode};')

EVACUATION_CENTERS_OVERPASS_QUERY_POLYGON = (
    '('
    'node["evacuation_center"="yes"]'
    '(poly:"{polygon}");'
    'way["evacuation_center"="yes"]'
    '(poly:"{polygon}");'
    'relation["evacuation_center"="yes"]'
    '(poly:"{polygon}");'
    ');'
    '(._;>;);'
    'out {print_mode};')


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
    'out {print_mode};')

BUILDINGS_OVERPASS_QUERY_POLYGON = (
    '('
    'node["building"]'
    '(poly:"{polygon}");'
    'way["building"]'
    '(poly:"{polygon}");'
    'relation["building"]'
    '(poly:"{polygon}");'
    ');'
    '(._;>;);'
    'out {print_mode};')

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
    'out {print_mode};')

ROADS_OVERPASS_QUERY_POLYGON = (
    '('
    'node["highway"]'
    '(poly:"{polygon}");'
    'way["highway"]'
    '(poly:"{polygon}");'
    'relation["highway"]'
    '(poly:"{polygon}");'
    ');'
    '(._;>;);'
    'out {print_mode};')

FLOOD_PRONE_OVERPASS_QUERY = (
    '('
    'way["flood_prone"="yes"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'relation["flood_prone"="yes"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out {print_mode};')

FLOOD_PRONE_OVERPASS_QUERY_POLYGON = (
    '('
    'way["flood_prone"="yes"]'
    '(poly:"{polygon}");'
    'relation["flood_prone"="yes"]'
    '(poly:"{polygon}");'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_1_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="1"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["boundary"="administrative"]["admin_level"="1"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_2_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="2"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["boundary"="administrative"]["admin_level"="2"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_3_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="3"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["boundary"="administrative"]["admin_level"="3"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_4_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="4"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["boundary"="administrative"]["admin_level"="4"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_5_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="5"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["boundary"="administrative"]["admin_level"="5"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_6_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="6"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["boundary"="administrative"]["admin_level"="6"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_7_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="7"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["boundary"="administrative"]["admin_level"="7"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_8_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="8"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["boundary"="administrative"]["admin_level"="8"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_9_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="9"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["boundary"="administrative"]["admin_level"="9"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_10_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="10"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["boundary"="administrative"]["admin_level"="10"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_11_OVERPASS_QUERY = (
    '('
    'relation["boundary"="administrative"]["admin_level"="11"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    'way["boundary"="administrative"]["admin_level"="11"]'
    '({SW_lat},{SW_lng},{NE_lat},{NE_lng});'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_1_OVERPASS_QUERY_POLYGON = (
    '('
    'relation["boundary"="administrative"]["admin_level"="1"]'
    '(poly:"{polygon}");'
    'way["boundary"="administrative"]["admin_level"="1"]'
    '(poly:"{polygon}");'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_2_OVERPASS_QUERY_POLYGON = (
    '('
    'relation["boundary"="administrative"]["admin_level"="2"]'
    '(poly:"{polygon}");'
    'way["boundary"="administrative"]["admin_level"="2"]'
    '(poly:"{polygon}");'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_3_OVERPASS_QUERY_POLYGON = (
    '('
    'relation["boundary"="administrative"]["admin_level"="3"]'
    '(poly:"{polygon}");'
    'way["boundary"="administrative"]["admin_level"="3"]'
    '(poly:"{polygon}");'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_4_OVERPASS_QUERY_POLYGON = (
    '('
    'relation["boundary"="administrative"]["admin_level"="4"]'
    '(poly:"{polygon}");'
    'way["boundary"="administrative"]["admin_level"="4"]'
    '(poly:"{polygon}");'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_5_OVERPASS_QUERY_POLYGON = (
    '('
    'relation["boundary"="administrative"]["admin_level"="5"]'
    '(poly:"{polygon}");'
    'way["boundary"="administrative"]["admin_level"="5"]'
    '(poly:"{polygon}");'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_6_OVERPASS_QUERY_POLYGON = (
    '('
    'relation["boundary"="administrative"]["admin_level"="6"]'
    '(poly:"{polygon}");'
    'way["boundary"="administrative"]["admin_level"="6"]'
    '(poly:"{polygon}");'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_7_OVERPASS_QUERY_POLYGON = (
    '('
    'relation["boundary"="administrative"]["admin_level"="7"]'
    '(poly:"{polygon}");'
    'way["boundary"="administrative"]["admin_level"="7"]'
    '(poly:"{polygon}");'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_8_OVERPASS_QUERY_POLYGON = (
    '('
    'relation["boundary"="administrative"]["admin_level"="8"]'
    '(poly:"{polygon}");'
    'way["boundary"="administrative"]["admin_level"="8"]'
    '(poly:"{polygon}");'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_9_OVERPASS_QUERY_POLYGON = (
    '('
    'relation["boundary"="administrative"]["admin_level"="9"]'
    '(poly:"{polygon}");'
    'way["boundary"="administrative"]["admin_level"="9"]'
    '(poly:"{polygon}");'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_10_OVERPASS_QUERY_POLYGON = (
    '('
    'relation["boundary"="administrative"]["admin_level"="10"]'
    '(poly:"{polygon}");'
    'way["boundary"="administrative"]["admin_level"="10"]'
    '(poly:"{polygon}");'
    ');'
    '(._;>;);'
    'out {print_mode};')

BOUNDARY_11_OVERPASS_QUERY_POLYGON = (
    '('
    'relation["boundary"="administrative"]["admin_level"="11"]'
    '(poly:"{polygon}");'
    'way["boundary"="administrative"]["admin_level"="11"]'
    '(poly:"{polygon}");'
    ');'
    '(._;>;);'
    'out {print_mode};')

OVERPASS_QUERY_MAP_POLYGON = {
    'potential-idp': POTENTIAL_IDP_OVERPASS_QUERY_POLYGON,
    'evacuation-centers': EVACUATION_CENTERS_OVERPASS_QUERY_POLYGON,
    'buildings': BUILDINGS_OVERPASS_QUERY_POLYGON,
    'building-points': BUILDINGS_OVERPASS_QUERY_POLYGON,
    'flood-prone': FLOOD_PRONE_OVERPASS_QUERY_POLYGON,
    'roads': ROADS_OVERPASS_QUERY_POLYGON,
    'boundary-1': BOUNDARY_1_OVERPASS_QUERY_POLYGON,
    'boundary-2': BOUNDARY_2_OVERPASS_QUERY_POLYGON,
    'boundary-3': BOUNDARY_3_OVERPASS_QUERY_POLYGON,
    'boundary-4': BOUNDARY_4_OVERPASS_QUERY_POLYGON,
    'boundary-5': BOUNDARY_5_OVERPASS_QUERY_POLYGON,
    'boundary-6': BOUNDARY_6_OVERPASS_QUERY_POLYGON,
    'boundary-7': BOUNDARY_7_OVERPASS_QUERY_POLYGON,
    'boundary-8': BOUNDARY_8_OVERPASS_QUERY_POLYGON,
    'boundary-9': BOUNDARY_9_OVERPASS_QUERY_POLYGON,
    'boundary-10': BOUNDARY_10_OVERPASS_QUERY_POLYGON,
    'boundary-11': BOUNDARY_11_OVERPASS_QUERY_POLYGON,
}

OVERPASS_QUERY_MAP = {
    'potential-idp': POTENTIAL_IDP_OVERPASS_QUERY,
    'evacuation-centers': EVACUATION_CENTERS_OVERPASS_QUERY,
    'buildings': BUILDINGS_OVERPASS_QUERY,
    'building-points': BUILDINGS_OVERPASS_QUERY,
    'flood-prone': FLOOD_PRONE_OVERPASS_QUERY,
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

EVACUATION_CENTERS_SQL_QUERY = (
    '"SELECT ST_Transform(way, 4326) AS the_geom, '
    'evacuation_center AS evacuation,'
    'name,'
    'type,'
    'capacity,'
    'kitchen,'
    'water_source AS w_source,'
    'toilet,'
    'toilets_number AS toilets_no,'
    'house_name,'
    'house_number AS house_no,'
    'street,'
    'amenity,'
    'office,'
    'religion,'
    'leisure,'
    'building,'
    'building_use AS build_use,'
    'walls,'
    'levels,'
    'roof,'
    'access_roof AS roof_acc,'
    'structure '
    'FROM evacuation_center;"')

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
    '\\"addr:housenumber\\" AS house_no, '
    '\\"addr:street\\" AS street, '
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
    '\\"addr:housenumber\\" AS house_no, '
    '\\"addr:street\\" AS street, '
    'name, '
    'amenity, '
    'leisure, '
    '\\"building:use\\" AS use, '
    'office '
    'FROM planet_osm_polygon '
    'WHERE building != \'no\';"')

FLOOD_PRONE_SQL_QUERY = (
    '"SELECT ST_Transform(way, 4326) AS the_geom, '
    'flood_prone as floodprone, '
    '\\"flood:rain\\" AS rain, '
    '\\"flood:send\\" AS send, '
    'flood_depth AS depth, '
    'flood_duration AS duration, '
    'flood_latest AS last, '
    'fire_hazard AS firehazard, '
    'kab_name, '
    'kec_name, '
    'kel_name, '
    'rt_number, '
    'rw_number '
    'FROM planet_osm_polygon"')

BOUNDARY_SQL_QUERY = (
    '"SELECT ST_Transform(way, 4326) AS the_geom, '
    'name, '
    'population, '
    'ref, '
    'admin_level AS level '
    'FROM planet_osm_polygon"')

SQL_QUERY_MAP = {
    'potential-idp': POTENTIAL_IDP_SQL_QUERY,
    'evacuation-centers': EVACUATION_CENTERS_SQL_QUERY,
    'buildings': BUILDINGS_SQL_QUERY,
    'building-points': BUILDING_POINTS_SQL_QUERY,
    'roads': ROADS_SQL_QUERY,
    'flood-prone': FLOOD_PRONE_SQL_QUERY,
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
    'evacuation-centers': 'evacuation-centers',
    'flood-prone': 'flood-prone',
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
