var fs = require('fs');
var path = require('path');
var zlib = require("zlib");
var execSync = require('child_process').execSync;
var geojson2vt = require('@hotosm/geojson2vt');
var geojsonMerge = require('@mapbox/geojson-merge');
var turfExtent = require("turf-extent");


function read_geojson(file) {
  return JSON.parse(zlib.gunzipSync(fs.readFileSync(file)));
}

function make_vector_tiles(data, type_id) {
  const mergedData = geojsonMerge.merge(data);
  const [west, south, east, north] = turfExtent(mergedData);
  const options = {
    layers: {
      campaign: mergedData
    },
    rootDir: path.join('/tmp', type_id, 'tiles'),
    bbox : [south, west, north, east],
    zoom : {
      min : 10,
      max : 17
    }
  };
  geojson2vt(options);
}

function main(event) {
  const type_id = event.type.replace(' ', '_');
  const AWSBUCKETPREFIX = `${process.env.S3_BUCKET}/campaigns/${event.campaign_uuid}/render/${type_id}/`;
  const localDir = path.join('/tmp', type_id);

  execSync(
    `aws s3 sync "s3://${AWSBUCKETPREFIX}" "${localDir}" --content-encoding "gzip" --exclude "*" --include "geojson*"`,
    {maxBuffer: 1024 * 5000}
  );
  fs.readdir(localDir, (err, files) => {
    if (err) {
      console.log(`Could not read the dir ${localDir}`);
    } else {
      const geojson_files = files.filter(
        i => i.startsWith('geojson')
      ).map(
        i => read_geojson(path.join(localDir, i))
      );
      make_vector_tiles(geojson_files, type_id);
      console.log('Uploading tiles to S3.');
      execSync(
        `aws s3 cp --recursive ${path.join(localDir, 'tiles')} s3://${AWSBUCKETPREFIX}tiles --content-encoding gzip`,
        {maxBuffer: 1024 * 5000}
      );
      console.log('Upload finished.');
    }
  });
}

module.exports = main;
