import json
import os
import xml.sax

from parser import FeatureCompletenessParser
from utilities import (
	fix_tags,
	build_render_data_path,
    update_campaign
)


def main():
    path = '/Users/jorge/Desktop'

    with open(os.path.join(path, 'campaign_1.json'), 'r') as f:
        campaign = json.load(f)

    type_name = 'building'
    type_id = type_name.replace(' ', '_')

    for type_key in campaign['types']:
        if campaign['types'][type_key]['type'] == type_name:
            typee = campaign['types'][type_key]

    required_tags = fix_tags(typee['tags'])

    if 'element_type' in typee:
        element_type = typee['element_type']
    else:
        element_type = None

    xml_file = open(os.path.join(path, 'building.xml'), 'r')
    parser = FeatureCompletenessParser(
        required_tags,
        '.',
        'Polygon',
        type_name
	)

    try:
        xml.sax.parse(xml_file, parser)
    except xml.sax.SAXParseException:
        print('FAIL')
        parser.endDocument()

    params = dict(type_name=type_name,
        type_id=type_id,
        features_collected=parser.features_collected,
        features_completed=parser.features_completed
    )

    # Fetch again campaign information.
    # Maybe some previous update when this task started.
    # campaign = fetch_campaign(campaign_path(uuid))
    update_campaign(campaign, params)


if __name__ == "__main__":
	main()