-- Delete an additional column about polygons
ALTER TABLE planet_osm_polygon DROP COLUMN IF EXISTS "way_area";

-- Delete nodes which are part of a polygon
DELETE FROM planet_osm_point WHERE evacuation_center IS NULL;

-- Merge planet_osm_point and planet_osm_polygon into one idp table
DROP TABLE IF EXISTS evacuation_center;
CREATE TABLE evacuation_center AS
SELECT osm_id, evacuation_center, "name", "access:roof" AS access_roof, "addr:street" AS street, "addr:housename" AS house_name, "addr:housenumber" AS house_number,
	amenity, building, "building:levels" as levels, "building:roof" as roof, "building:structure" as structure, "building:use" as building_use, "building:walls" as walls,
	"capacity:persons" as capacity, "kitchen:facilities" as kitchen, leisure, office, "toilet:facilities" as toilet,
	"toilets:number" as toilets_number, ref, religion, water_source,
	ST_PointOnSurface(way) as way
FROM planet_osm_polygon
UNION
SELECT osm_id, evacuation_center, "name", "access:roof" AS access_roof, "addr:street" AS street, "addr:housename" AS house_name, "addr:housenumber" AS house_number,
	amenity, building, "building:levels" as levels, "building:roof" as roof, "building:structure" as structure, "building:use" as building_use, "building:walls" as walls,
	"capacity:persons" as capacity, "kitchen:facilities" as kitchen, leisure, office, "toilet:facilities" as toilet,
	"toilets:number" as toilets_number, ref, religion, water_source,
	way
FROM planet_osm_point;

-- Add type column
ALTER TABLE evacuation_center ADD COLUMN "type" VARCHAR(255) NULL;

UPDATE evacuation_center SET "type" = 'School' WHERE amenity  ILIKE
'%school%' OR amenity  ILIKE '%kindergarten%';

UPDATE evacuation_center SET "type" = 'University/College' WHERE
amenity  ILIKE '%university%' OR amenity  ILIKE '%college%';

UPDATE evacuation_center SET "type" = 'Hospital' WHERE amenity  ILIKE
'%hospital%';

UPDATE evacuation_center SET "type" = 'Bank' WHERE amenity  ILIKE
'%bank%';

UPDATE evacuation_center SET "type" = 'Clinic' WHERE amenity  ILIKE
'%clinic%';

UPDATE evacuation_center SET "type" = 'Public Building' WHERE
building  ILIKE '%public%' OR office ILIKE '%government%';

UPDATE evacuation_center SET "type" = 'Place of Worship - Islam'
where amenity  ILIKE '%worship%' and (religion  ILIKE '%islam'
or religion  ILIKE '%muslim%');

UPDATE evacuation_center SET "type" = 'Place of Worship - Unitarian'
where amenity  ILIKE '%worship%' and religion  ILIKE '%unitarian%';

UPDATE evacuation_center SET "type" = 'Place of Worship - Buddhist' WHERE
amenity  ILIKE '%worship%' and religion  ILIKE '%budd%';

-- run near the end

UPDATE evacuation_center SET "type" = 'School' WHERE
  "building_use" = 'education' AND "type" IS NULL ;

UPDATE evacuation_center SET "type" = 'Place of Worship' WHERE
  "building_use" = 'place_of_worship' AND "type" IS NULL ;

UPDATE evacuation_center SET "type" = 'Place of Worship' WHERE
  amenity = 'place_of_worship' AND "type" IS NULL ;

UPDATE evacuation_center SET "type" = 'School' WHERE
  "building_use" = 'school' AND "type" IS NULL ;

UPDATE evacuation_center SET "type" = 'Hospital' WHERE
  "building_use" = 'hospital' AND "type" IS NULL ;

-- By default
UPDATE evacuation_center SET "type" = 'Other' WHERE "type" IS NULL ;