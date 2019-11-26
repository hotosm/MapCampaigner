from collections import ChainMap
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import fromstring, ElementTree
import json


from aws import S3Data

def calc_completeness(req_tags, tags):
    status = "Incomplete"
    result = all(k in tags for k in req_tags)
    if result:
        status = "Complete"
    return status

def lambda_handler(event, context):
    uuid = event['campaign_uuid']
    campaign = S3Data().fetch(f'campaigns/{uuid}/campaign.json')
    types = campaign['types']
    all_features = []
    for _, feature_type in types.items():
        features = []
        key = f"campaigns/{uuid}/overpass/{feature_type['type']}.xml"
        feature_xml = S3Data().fetch(key)
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
                feature['type'] = child.tag
                feature['feature_type'] = feature_type['type']
                required_tags = [":".join(k.split(":", 2)[:2]) for k, _ in
                                feature_type['tags'].items()]
                feature['status'] = calc_completeness(required_tags, tags)
                feature['last_edited_by'] = child.attrib['user']
                feature['last_edit_date'] = child.attrib['timestamp']
                feature['attributes'] = [elem for elem in required_tags if
                                         elem in tags]
                feature['missing_attributes'] = [elem for elem in required_tags
                                                 if elem not in tags]
                features.append(feature)
        all_features.append(features)
        out_file = 'campaigns/{}/{}.json'.format(uuid,feature_type["type"])
        S3Data().create(out_file, json.dumps(features))
    flat_list = [item for sublist in all_features for item in sublist]
    out_file = 'campaigns/{}/all_features.json'.format(uuid)
    S3Data().create(out_file, json.dumps(flat_list))