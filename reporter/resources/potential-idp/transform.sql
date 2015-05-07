-- Delete an additional column about polygons
ALTER TABLE planet_osm_polygon DROP COLUMN IF EXISTS "way_area";

-- Delete nodes which are part of a polygon
DELETE FROM planet_osm_point WHERE amenity IS NULL AND building IS NULL AND leisure IS NULL;

-- Merge planet_osm_point and planet_osm_polygon into one idp table
DROP TABLE IF EXISTS idp;
CREATE TABLE idp AS
SELECT osm_id, access, "access:roof", "addr:full", "addr:housename", "addr:housenumber", "addr:interpolation",
	amenity, building, "building:levels", "building:roof", "building:structure", "building:use", "building:walls",
	"capacity:persons", denomination, leisure, ref, religion, sport,
	ST_PointOnSurface(way)as way
FROM planet_osm_polygon
UNION
SELECT osm_id, access, "access:roof", "addr:full", "addr:housename", "addr:housenumber", "addr:interpolation",
	amenity, building, "building:levels", "building:roof", "building:structure", "building:use", "building:walls",
	"capacity:persons", denomination, leisure, ref, religion, sport,
	way
FROM planet_osm_point;

-- Add type column
ALTER TABLE idp ADD COLUMN "type" VARCHAR(255) NULL;

UPDATE idp SET "type" = 'School' WHERE amenity  ILIKE
'%school%' OR amenity  ILIKE '%kindergarten%';

UPDATE idp SET "type" = 'University/College' WHERE
amenity  ILIKE '%university%' OR amenity  ILIKE '%college%';

UPDATE idp SET "type" = 'Hospital' WHERE amenity  ILIKE
'%hospital%';

UPDATE idp SET "type" = 'Public Building' WHERE
building  ILIKE '%public%';

UPDATE idp SET "type" = 'Place of Worship - Islam'
where amenity  ILIKE '%worship%' and (religion  ILIKE '%islam'
or religion  ILIKE '%muslim%');

UPDATE idp SET "type" = 'Place of Worship - Unitarian'
where amenity  ILIKE '%worship%' and religion  ILIKE '%unitarian%';

UPDATE idp SET "type" = 'Place of Worship - Buddhist' WHERE
amenity  ILIKE '%worship%' and religion  ILIKE '%budd%';

-- run near the end

UPDATE idp SET "type" = 'School' WHERE
  "building:use" = 'education' AND "type" IS NULL ;

UPDATE idp SET "type" = 'Place of Worship' WHERE
  "building:use" = 'place_of_worship' AND "type" IS NULL ;

UPDATE idp SET "type" = 'Place of Worship' WHERE
  amenity = 'place_of_worship' AND "type" IS NULL ;

UPDATE idp SET "type" = 'School' WHERE
  "building:use" = 'school' AND "type" IS NULL ;

UPDATE idp SET "type" = 'Hospital' WHERE
  "building:use" = 'hospital' AND "type" IS NULL ;