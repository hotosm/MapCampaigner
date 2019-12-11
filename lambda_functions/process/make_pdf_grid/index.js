const bbox = require('@turf/bbox').default;
const intersect = require('@turf/boolean-intersects').default;
const rectangleGrid = require('temp-turf-rectangle-grid').default;
const featureCollection = require('@turf/helpers').featureCollection;
const bboxPolygon = require('@turf/bbox-polygon').default;
const distance = require('@turf/distance').default;
const centerOfMass = require('@turf/center-of-mass').default;
const destination = require('@turf/destination').default;
const AWS = require('aws-sdk');

async function getS3File(uuid) {
    const s3 = new AWS.S3();
    const params = {
        Bucket: process.env.S3_BUCKET,
        Key: `campaigns/${uuid}/campaign.geojson` 
    }

    const response = await s3.getObject(params, (err) => {
      if (err) {
        throw err;
      }
    }).promise();
    return response.Body.toString(); 
}


async function main(event) {
    const response = await getS3File(event.campaign_uuid);
    const f = JSON.parse(response).features;
    const options = {units:"meters"};
    const features = [];
    const dissFeatures = [];
    const gridWidth = 500;
    const gridHeight = 500;
    for (let i = 0; i < f.length; i++) {
        const box = bbox(f[i]);
        const w = distance([box[0], box[1]],[box[2],box[1]],options);
        const h = distance([box[0], box[1]],[box[0],box[3]],options);
        const wDiff = gridWidth - (w % gridWidth);
        const hDiff = gridHeight - (h % gridHeight);
        const poly = bboxPolygon(box);
        const c = centerOfMass(poly);
        const maxY = destination(c,(50 + h + hDiff)/2, 0, options).geometry.coordinates[1];
        const minY = destination(c,(50 +h + hDiff)/2, 180,options).geometry.coordinates[1];
        const maxX = destination(c,(50 + w + wDiff)/2, 90,options).geometry.coordinates[0];
        const minX = destination(c,(50 + w + wDiff)/2, -90,options).geometry.coordinates[0];
        const grid = rectangleGrid([minX, minY, maxX, maxY], gridWidth, gridHeight, options);
        const diss = bboxPolygon(bbox(grid));
        dissFeatures.push(diss);
        for (let j=0; j<grid.features.length; j++) {
            const k = intersect(grid.features[j], f[i]);
            
            if (k) {
                grid.features[j].properties.id = i;
                features.push(grid.features[j]);
            }
        }
    }
    const fc = featureCollection(features);
    const dissFc = featureCollection(dissFeatures);
    const s3 = new AWS.S3();
    const uploaded = await s3.putObject({
        Bucket: process.env.S3_BUCKET,
        Key: `campaigns/${event.campaign_uuid}/pdf/grid.geojson`,
        ACL: 'public-read',
        Body: JSON.stringify(fc)
    }).promise();
    await s3.putObject({
        Bucket: process.env.S3_BUCKET,
        Key: `campaigns/${event.campaign_uuid}/pdf/grid_diss.geojson`,
        ACL: 'public-read',
        Body: JSON.stringify(dissFc)
    }).promise();
    
    console.log(`Invoking lambda handler...`);

    const lambda = new AWS.Lambda();
    const payload = `{"campaign_uuid": "${event.campaign_uuid}",
    "zoom_levels": [10,11,12,13,14,15,16,17]}`;
    var params = {
        FunctionName: `${process.env.ENV}_process_make_mbtiles`,
        InvocationType: 'Event',
        Payload: payload
    };

    await lambda.invoke(params).promise();
    console.log(`finished... ${JSON.stringify(uploaded)}`);
  }
  
  
  exports.handler = async (event) => {
     await main(event);
  };
