ALTER TABLE planet_osm_line ADD COLUMN "type" VARCHAR(255) NULL;

UPDATE
  planet_osm_line
SET
  "type" = 'Motorway or highway'
WHERE
  highway ILIKE 'motorway' OR highway ILIKE 'highway' or highway ILIKE 'trunk';

--

UPDATE
  planet_osm_line
SET
  "type" = 'Motorway link'
WHERE
  highway ILIKE 'motorway_link';

--

UPDATE
  planet_osm_line
SET
  "type" = 'Primary road'
WHERE
  highway ILIKE 'primary';

--

UPDATE
  planet_osm_line
SET
  "type" = 'Primary link'
WHERE
  highway ILIKE 'primary_link';

--

UPDATE
  planet_osm_line
SET
  "type" = 'Tertiary'
WHERE
  highway ILIKE 'tertiary';

--

UPDATE
  planet_osm_line
SET
  "type" = 'Tertiary link'
WHERE
  highway ILIKE 'tertiary_link';

--

UPDATE
  planet_osm_line
SET
  "type" = 'Secondary'
WHERE
  highway ILIKE 'secondary';


--

UPDATE
  planet_osm_line
SET
  "type" = 'Secondary link'
WHERE
  highway ILIKE 'secondary_link';


--

UPDATE
  planet_osm_line
SET
  "type" = 'Road, residential, living street, etc.'
WHERE
  highway ILIKE 'living_street'
OR
  highway ILIKE 'residential'
OR
  highway ILIKE 'yes'
OR
  highway ILIKE 'road'
OR
  highway ILIKE 'unclassified'
OR
  highway ILIKE 'service'
OR
  highway ILIKE ''
OR
  highway IS NULL
;


--

UPDATE
  planet_osm_line
SET
  "type" = 'Track'
WHERE
  highway ILIKE 'track';

--

UPDATE
  planet_osm_line
SET
  "type" = 'Cycleway, footpath, etc.'
WHERE
  highway ILIKE 'cycleway'
OR
  highway ILIKE 'footpath'
OR
  highway ILIKE 'pedestrian'
OR
  highway ILIKE 'footway'
OR
  highway ILIKE 'path'
;
