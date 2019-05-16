var fs = require('fs');
var path = require('path');
var zlib = require("zlib");
var AWS = require('aws-sdk');
var geojson2vt = require('@hotosm/geojson2vt');
var geojsonMerge = require('@mapbox/geojson-merge');
var turfExtent = require("turf-extent");

function read_geojson(file) {
  var data = JSON.parse(zlib.gunzipSync(fs.readFileSync(file)));
  data.features.forEach(i => i.properties.id = i.id);
  return data;
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

async function downloadGeojsonFiles(uuid, type_id, localDir) {
  var S3 = new AWS.S3();
  var result = [];

  let listedObjects = await S3.listObjects({
    Bucket: process.env.S3_BUCKET,
    Prefix: `campaigns/${uuid}/render/${type_id}/`
  }).promise();

  listedObjects = listedObjects.Contents.filter(item =>
      path.parse(item.Key).ext === '.json' && path.parse(item.Key).name.startsWith('geojson')
    ).map(
      item => item.Key
    );

  await Promise.all(listedObjects.map(async (item) => {
    const getObject = await S3.getObject({
      Bucket: process.env.S3_BUCKET,
      Key: item
    }).promise();
    fs.writeFileSync(path.join(localDir, path.parse(item).base), getObject.Body);
    console.log(`Downloaded ${item}`);
  }));
}

async function readGeojsonFiles(localDir) {
  const geojson = await new Promise((resolve, reject) => {
    fs.readdir(localDir, (err, files) => {
      if (err) {
        console.log(`-- Could not read the dir ${localDir}`);
      } else {
        resolve(files.filter(
          i => i.startsWith('geojson')
        ).map(
          i => read_geojson(path.join(localDir, i))
        ));
      }
    });
  });
  return geojson;
}

async function uploadTiles(localDir, uuid, type_id) {
  console.log('-- Uploading tiles to S3.');
  const S3 = new AWS.S3();
  let result = [];
  const zoomLevels = fs.readdirSync(path.join(localDir, 'tiles'));
  await Promise.all(zoomLevels.map(async (zoomLevel) => {
    const tiles = fs.readdirSync(path.join(localDir, 'tiles', zoomLevel));
    await Promise.all(tiles.map(async (tile) => {
      const pbfs = fs.readdirSync(path.join(localDir, 'tiles', zoomLevel, tile));
       result.push(await Promise.all(pbfs.map(async (pbf) => {
        console.log(`Uploading to ${process.env.S3_BUCKET}/campaigns/${uuid}/render/${type_id}/tiles/${zoomLevel}/${tile}/${pbf}`);
        return new Promise((resolve, reject) => {
          return S3.putObject({
            Bucket: process.env.S3_BUCKET,
            Key: `campaigns/${uuid}/render/${type_id}/tiles/${zoomLevel}/${tile}/${pbf}`,
            Body: fs.readFileSync(path.join(localDir, 'tiles', zoomLevel, tile, pbf)),
            ContentEncoding: 'gzip'
          }).promise()
          .then((data) => {
            return resolve(JSON.stringify(data));
          });
        });
      })));
    }));
  }));
  return Promise.resolve(result);
}


async function main(event) {
  const type_id = event.type.replace(' ', '_');
  const AWSBUCKETPREFIX = `${process.env.S3_BUCKET}/campaigns/${event.campaign_uuid}/render/${type_id}/`;
  const localDir = path.join('/tmp', type_id);

  if (!fs.existsSync(localDir)) {
    fs.mkdir(localDir, (err) => {if (err) throw err;});
  }

  const result = await downloadGeojsonFiles(
    event.campaign_uuid,
    type_id,
    localDir
  );
  const geojsonData = await readGeojsonFiles(localDir);
  await make_vector_tiles(geojsonData, type_id);
  const uploadedTiles = await uploadTiles(localDir, event.campaign_uuid, type_id);
  console.log(`finished... ${uploadedTiles}`);
}


exports.handler = async (event) => {
  var tiles = await main(event);
  return tiles;
};
