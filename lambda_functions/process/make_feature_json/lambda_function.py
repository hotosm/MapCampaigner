import xml.etree.ElementTree as ET
from xml.etree.ElementTree import fromstring, ElementTree
import json

from aws import S3Data


def lambda_handler(event, context):
    try:
        main(event, context)
    except Exception as e:
        S3Data().create(
            key=f'campaigns/{event["campaign_uuid"]}/failure.json',
            body=json.dumps({
                'function': 'process_make_feature_json',
                'failure': str(e)
                })
            )


def main(event, context):
    """For a campaign, uses the Overpass data
    to create JSON files (1 for all feature types,
    and 1 for each feature type) for data inputs
    on the project overview and feature pages."""
    uuid = event['campaign_uuid']
    event_type = event['type']

    campaign = S3Data().fetch(f'campaigns/{uuid}/campaign.json')
    filtered = [v for k, v in campaign['types'].items()
        if v['type'] == event_type]
    if len(filtered) == 0:
        raise ValueError('Feature not found')

    feature_type = filtered[0]
    feature_file = feature_type['type'].replace(' ', '_')
    features = []

    key = f"campaigns/{uuid}/overpass/{feature_file}.xml"

    s3 = S3Data().s3
    feature_xml = s3.get_object(Bucket=S3Data().bucket, Key=key)['Body'].read()
    parser = ET.XMLParser(encoding="utf-8")
    tree = ElementTree(fromstring(feature_xml, parser=parser))
    root = tree.getroot()
    for child in root:
        if child.tag in ('way', 'node'):
            tags = []
            if len(child) == 0:
                continue
            for tag in child:
                if tag.tag == 'tag':
                    tags.append(tag.attrib['k'])
            feature = {}
            feature['id'] = child.attrib['id']
            geometry = 'Point'
            if child.tag == 'way':
                geometry = 'Line'
                nds = []
                for sub in child:
                    if sub.tag == 'nd':
                        nds.append(sub.tag)
                if len(nds) > 0:
                    if nds[0] == nds[-1]:
                        geometry = 'Polygon'
            feature['geometry_type'] = geometry
            feature['osm_type'] = child.tag
            feature['type'] = feature_type['type']
            feature['feature'] = feature_type['feature']
            required_tags = [":".join(k.split(":", 2)[:2]) for k, _ in
                             feature_type['tags'].items()]
            feature['status'] = calc_completeness(required_tags, tags)
            feature['last_edited_by'] = child.attrib['user']
            feature['last_edit_date'] = child.attrib['timestamp']
            feature['attributes'] = [elem for elem in required_tags if
                                     elem in tags]
            feature['missing_attributes'] = [elem for elem in required_tags
                                             if elem not in tags]
            if feature_type['element_type'] == geometry:
                features.append(feature)
    out_file = 'campaigns/{}/{}.json'.format(uuid, feature_file)
    S3Data().create(out_file, json.dumps(features))


def calc_completeness(req_tags, tags):
    """Takes in a list of required tags and
    tags found. Returns a string status of
    completion depending if all required tags
    were found."""
    status = "Incomplete"
    result = all(k in tags for k in req_tags)
    if result:
        status = "Complete"
    return status


def feature_stats(features, types):
    feature_type = features[0]['type']
    for k, v in types.items():
        if v['type'] == feature_type:
            types[k]["feature_count"] = len(features)
            types[k]["complete"] = len([f for f in features if
                                    f['status'] == "Complete"])
            types[k]["incomplete"] = len([f for f in features if
                                      f['status'] == "Incomplete"])
    return types
