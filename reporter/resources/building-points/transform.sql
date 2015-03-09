ALTER TABLE planet_osm_polygon ADD COLUMN "type" VARCHAR(255) NULL;

UPDATE planet_osm_polygon SET "type" = 'School' WHERE amenity  ILIKE
'%school%' OR amenity  ILIKE '%kindergarten%';

UPDATE planet_osm_polygon SET "type" = 'University/College' WHERE
amenity  ILIKE '%university%' OR amenity  ILIKE '%college%';

UPDATE planet_osm_polygon SET "type" = 'Government' WHERE amenity
 ILIKE '%government%' OR office  ILIKE 'government';

UPDATE planet_osm_polygon SET "type" = 'Clinic/Doctor' WHERE amenity
 ILIKE '%clinic%' OR amenity  ILIKE '%doctor%';

UPDATE planet_osm_polygon SET "type" = 'Hospital' WHERE amenity  ILIKE
'%hospital%';
UPDATE planet_osm_polygon SET "type" = 'Fire Station' WHERE amenity
 ILIKE '%fire%';

UPDATE planet_osm_polygon SET "type" = 'Police Station' WHERE
amenity  ILIKE '%police%';

UPDATE planet_osm_polygon SET "type" = 'Public Building' WHERE
amenity  ILIKE '%public building%';

UPDATE planet_osm_polygon SET "type" = 'Place of Worship - Islam'
where amenity  ILIKE '%worship%' and (religion  ILIKE '%islam'
or religion  ILIKE '%muslim%');

UPDATE planet_osm_polygon SET "type" = 'Place of Worship - Unitarian'
where amenity  ILIKE '%worship%' and religion  ILIKE '%unitarian%';

UPDATE planet_osm_polygon SET "type" = 'Place of Worship - Buddhist' WHERE
amenity  ILIKE '%worship%' and religion  ILIKE '%budd%';

UPDATE planet_osm_polygon SET "type" = 'Place of Worship - Unitarian' WHERE
amenity  ILIKE '%worship%' and religion  ILIKE '%unitarian%';

UPDATE planet_osm_polygon SET "type" = 'Supermarket' WHERE amenity
 ILIKE '%mall%' OR amenity  ILIKE '%market%';

UPDATE planet_osm_polygon SET "type" = 'Residential' WHERE landuse  ILIKE
'%residential%' OR "building:use"='residential';

UPDATE planet_osm_polygon SET "type" = 'Sports Facility' WHERE landuse  ILIKE
'%recreation_ground%' OR (leisure IS NOT NULL AND leisure != '') ;

-- run near the end

UPDATE planet_osm_polygon SET "type" = 'Government' WHERE
  "building:use" = 'government' AND "type" IS NULL ;

UPDATE planet_osm_polygon SET "type" = 'Residential' WHERE
  "building:use" = 'residential' AND "type" IS NULL ;

UPDATE planet_osm_polygon SET "type" = 'School' WHERE
  "building:use" = 'education' AND "type" IS NULL ;

UPDATE planet_osm_polygon SET "type" = 'Clinic/Doctor' WHERE
  "building:use" = 'medical' AND "type" IS NULL ;

UPDATE planet_osm_polygon SET "type" = 'Place of Worship' WHERE
  "building:use" = 'place_of_worship' AND "type" IS NULL ;
  
UPDATE planet_osm_polygon SET "type" = 'School' WHERE
  "building:use" = 'school' AND "type" IS NULL ;

UPDATE planet_osm_polygon SET "type" = 'Hospital' WHERE
  "building:use" = 'hospital' AND "type" IS NULL ;
  
UPDATE planet_osm_polygon SET "type" = 'Commercial' WHERE
  "building:use" = 'commercial' AND "type" IS NULL ;

UPDATE planet_osm_polygon SET "type" = 'Industrial' WHERE
  "building:use" = 'industrial' AND "type" IS NULL ;
  
UPDATE planet_osm_polygon SET "type" = 'Utility' WHERE
  "building:use" = 'utility' AND "type" IS NULL ;

-- Add default type
UPDATE planet_osm_polygon SET "type" = 'Residential' WHERE "type" IS NULL ;