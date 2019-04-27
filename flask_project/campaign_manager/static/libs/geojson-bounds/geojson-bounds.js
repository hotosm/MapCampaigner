  /*
   This file is part of geojson-bounds
   Author: John J Czaplewski
   License: CC-By-4.0
   https://github.com/jczaplew/geojson-bounds
  */
  function flatten(input, output) {
    output = output || [];
    var idx = output.length;
    for (var i = 0; i < input.length; i++) {
      if (Array.isArray(input[i]) && Array.isArray(input[i][0])) {
        flatten(input[i], output);
        idx = output.length;
      } else {
        output[idx++] = input[i];
      }
    }
    return (Array.isArray(output[0])) ? output : [output];
  }

  function maxLat(coords) {
    return Math.max.apply(null, coords.map(function(d) { return d[1]; }));
  }

  function maxLng(coords) {
    return Math.max.apply(null, coords.map(function(d) { return d[0]; }));
  }

  function minLat(coords) {
    return Math.min.apply(null, coords.map(function(d) { return d[1]; }));
  }

  function minLng(coords) {
    return Math.min.apply(null, coords.map(function(d) { return d[0]; }));
  }

  function fetchEnvelope(coords) {
    var mmc = {
      "minLng": minLng(coords),
      "minLat": minLat(coords),
      "maxLng": maxLng(coords),
      "maxLat": maxLat(coords)
    };

    return {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [mmc.minLng, mmc.minLat],
          [mmc.minLng, mmc.maxLat],
          [mmc.maxLng, mmc.maxLat],
          [mmc.maxLng, mmc.minLat],
          [mmc.minLng, mmc.minLat]
        ]]
      }
    };
  }

  function fetchExtent(coords) {
    return [
      minLng(coords),
      minLat(coords),
      maxLng(coords),
      maxLat(coords)
    ];
  }

  // Adapted from http://stackoverflow.com/questions/2792443/finding-the-centroid-of-a-polygon
  function fetchCentroid(vertices) {
    var centroid = {
      x: 0,
      y: 0
    };

    var signedArea = 0;
    var x0 = 0;
    var y0 = 0;
    var x1 = 0;
    var y1 = 0;
    var a = 0;

    for (var i = 0; i < vertices.length - 1; i++) {
      x0 = vertices[i][0];
      y0 = vertices[i][1];
      x1 = vertices[i + 1][0];
      y1 = vertices[i + 1][1];
      a = (x0 * y1) - (x1 * y0);

      signedArea += a;
      centroid.x += (x0 + x1) * a;
      centroid.y += (y0 + y1) * a;
    }

    x0 = vertices[vertices.length - 1][0];
    y0 = vertices[vertices.length - 1][1];
    x1 = vertices[0][0];
    y1 = vertices[0][1];
    a = (x0 * y1) - (x1 * y0);
    signedArea += a;
    centroid.x += (x0 + x1) * a;
    centroid.y += (y0 + y1) * a;

    signedArea = signedArea * 0.5;
    centroid.x = centroid.x / (6.0*signedArea);
    centroid.y = centroid.y / (6.0*signedArea);

    return [centroid.x, centroid.y];
  }

  function feature(obj) {
    return flatten(obj.geometry.coordinates);
  }

  function featureCollection(f) {
    return flatten(f.features.map(feature));
  }

  function geometryCollection(g) {
    return flatten(g.geometries.map(process));
  }

  function process(t) {
    if (!t) {
      return [];
    }

    switch (t.type) {
      case "Feature":
        return feature(t);
      case "GeometryCollection":
        return geometryCollection(t);
      case "FeatureCollection":
        return featureCollection(t);
      case "Point":
      case "LineString":
      case "Polygon":
      case "MultiPoint":
      case "MultiPolygon":
      case "MultiLineString":
        return flatten(t.coordinates);
      default:
        return [];
    }
  }

  function envelope(t) {
    return fetchEnvelope(process(t));
  }

  function extent(t) {
    return fetchExtent(process(t));
  }

  function centroid(t) {
    return fetchCentroid(process(t));
  }

  function xMin(t) {
    return minLng(process(t));
  }
  function xMax(t) {
    return maxLng(process(t));
  }
  function yMin(t) {
    return minLat(process(t));
  }
  function yMax(t) {
    return maxLat(process(t));
  }
