alter table planet_osm_polygon add column type varchar(255) null;

update planet_osm_polygon set type = 'School' where amenity ilike
'%school%' or amenity ilike '%kindergarten%';

update planet_osm_polygon set type = 'University/College' where
amenity ilike '%university%' or amenity ilike '%college%';

update planet_osm_polygon set type = 'Government' where amenity
ilike '%government%' or office ilike 'government';

update planet_osm_polygon set type = 'Clinic/Doctor' where amenity
ilike '%clinic%' or amenity ilike '%doctor%';

update planet_osm_polygon set type = 'Hospital' where amenity ilike
'%hospital%';
update planet_osm_polygon set type = 'Fire Station' where amenity
ilike '%fire%';

update planet_osm_polygon set type = 'Police Station' where
amenity ilike '%police%';

update planet_osm_polygon set type = 'Public Building' where
amenity ilike '%public building%';

update planet_osm_polygon set type = 'Place of Worship - Islam'
where amenity ilike '%worship%' and (religion ilike '%islam'
or religion ilike '%muslim%');

update planet_osm_polygon set type = 'Place of Worship - Unitarian'
where amenity ilike '%worship%' and religion ilike '%unitarian%';

update planet_osm_polygon set type = 'Place of Worship - Buddhist' where
amenity ilike '%worship%' and religion ilike '%budd%';

update planet_osm_polygon set type = 'Place of Worship - Unitarian' where
amenity ilike '%worship%' and religion ilike '%unitarian%';

update planet_osm_polygon set type = 'Supermarket' where amenity
ilike '%mall%' or amenity ilike '%market%';

update planet_osm_polygon set type = 'Residential' where landuse ilike
'%residential%' or "building:use"='residential';

update planet_osm_polygon set type = 'Sports Facility' where landuse ilike
'%recreation_ground%' or (leisure is not null and leisure != '') ;

-- run near the end

update planet_osm_polygon set type = 'Government' where
  "building:use" = 'government' and type is null ;

update planet_osm_polygon set type = 'Residential' where
  "building:use" = 'residential' and type is null ;

update planet_osm_polygon set type = 'School' where
  "building:use" = 'education' and type is null ;

update planet_osm_polygon set type = 'Clinic/Doctor' where
  "building:use" = 'medical' and type is null ;

update planet_osm_polygon set type = 'Place of Worship' where
  "building:use" = 'place_of_worship' and type is null ;
  
update planet_osm_polygon set type = 'School' where
  "building:use" = 'school' and type is null ;

update planet_osm_polygon set type = 'Hospital' where
  "building:use" = 'hospital' and type is null ;
  
update planet_osm_polygon set type = 'Commercial' where
  "building:use" = 'commercial' and type is null ;

update planet_osm_polygon set type = 'Industrial' where
  "building:use" = 'industrial' and type is null ;
  
update planet_osm_polygon set type = 'Utility' where
  "building:use" = 'utility' and type is null ;
