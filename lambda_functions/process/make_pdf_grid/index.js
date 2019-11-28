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
    const f = JSON.parse(response).features
    const options = {units:"meters"}
    const features = []
    for (const feature of f) {
        const box = bbox(feature);
        const w = distance([box[0], box[1]],[box[2],box[1]],{units:"meters"})
        const h = distance([box[0], box[1]],[box[0],box[3]],{units:"meters"})
        const wDiff = 1000 - (w % 1000);
        const hDiff = 706 - (h % 706);
        const poly = bboxPolygon(box);
        const c = centerOfMass(poly);
        const maxY = destination(c,(50 + h + hDiff)/2, 0, options).geometry.coordinates[1];
        const minY = destination(c,(50 +h + hDiff)/2, 180,options).geometry.coordinates[1];
        const maxX = destination(c,(50 + w + wDiff)/2, 90,options).geometry.coordinates[0];
        const minX = destination(c,(50 + w + wDiff)/2, -90,options).geometry.coordinates[0];
        const grid = rectangleGrid([minX, minY, maxX, maxY], 1000, 706, {units:"meters"});
        for (let i=0; i<grid.features.length; i++) {
            const j = intersect(grid.features[i], feature);
            
            if (j) {
                grid.features[i].properties.id = i
                features.push(grid.features[i])
            }
        }
    }
    const fc = featureCollection(features)
    const s3 = new AWS.S3();
    const uploaded = await s3.putObject({
        Bucket: process.env.S3_BUCKET,
        Key: `campaigns/${event.campaign_uuid}/pdf/grid.geojson`,
        Body: JSON.stringify(fc)
    }).promise();
    console.log(`finished... ${uploaded}`);
  }
  
  
  exports.handler = async (event) => {
     await main(event);
     const lambda = new AWS.Lambda();
     var params = {
        FunctionName: `${process.env}_process_make_pdfs`,
        InvocationType: 'RequestResponse',
        Payload: `{"campaign_uuid:"${event.campaign_uuid}"}`
      };

      await lambda.invoke(params).promise()

  };
  