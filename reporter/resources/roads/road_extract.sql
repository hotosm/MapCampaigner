SELECT way AS
  the_geom, "name", highway as type
FROM
  planet_osm_line
WHERE
  highway != 'no';
