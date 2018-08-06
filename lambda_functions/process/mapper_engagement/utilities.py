import json
from aws import S3Data
import xml.sax

def fetch_campaign(campaign_path):
    return S3Data().fetch('{campaign_path}/campaign.json'.format(
        campaign_path=campaign_path))

def fetch_osm_data(campaign_path, filename):
    return S3Data().fetch('{campaign_path}/raw_data/attic/{filename}'.format(
        campaign_path=campaign_path,
        filename=filename))

from osm_way_parser import OsmParser

def osm_object_contributions(
        osm_file,
        tag_name,
        date_start=None,
        date_end=None):
    """Compile a summary of user contributions for the selected osm data type.

    :param osm_file: A file object reading from a .osm file.
    :type osm_file: file, FileIO

    :param tag_name: The tag name we want to filter on.
    :type tag_name: str

    :param date_start: The start date we want to filter
    :type date_start: float

    :param date_end: The end date we want to filter
    :type date_end: float

    :returns: A list of dicts where items in the list are sorted from highest
        contributor (based on number of ways) down to lowest. Each element
        in the list is a dict in the form: {
        'user': <user>,
        'ways': <way count>,
        'nodes': <node count>,
        'timeline': <timelinedict>,
        'best': <most ways in a single day>,
        'worst': <least ways in single day>,
        'average': <average ways across active days>,
        'crew': <bool> }
        where crew is used to designate users who are part of an active
        data gathering campaign.
        The timeline dict will contain a collection of dates and
        the total number of ways created on that date e.g.
        {
            u'2010-12-09': 10,
            u'2012-07-10': 14
        }
    :rtype: list
    """
    parser = OsmParser(
            start_date=date_start,
            end_date=date_end)
    try:
        xml.sax.parse(osm_file, parser)
    except xml.sax.SAXParseException:
        LOGGER.exception('Failed to parse OSM xml.')
        raise

    way_count_dict = parser.wayCountDict
    node_count_dict = parser.nodeCountDict
    timelines = parser.userDayCountDict

    # Convert to a list of dicts so we can sort it.
    crew_list = config.CREW
    user_list = []

    for key, value in way_count_dict.items():
        start_date, end_date = date_range(timelines[key])
        start_date = time.strftime('%d-%m-%Y', start_date.timetuple())
        end_date = time.strftime('%d-%m-%Y', end_date.timetuple())
        user_timeline = timelines[key]
        node_count = 0
        if key in node_count_dict:
            node_count = node_count_dict[key]
        record = {
            'name': key,
            'ways': value,
            'nodes': node_count,
            'timeline': interpolated_timeline(user_timeline),
            'start': start_date,
            'end': end_date,
            'activeDays': len(user_timeline),
            'best': best_active_day(user_timeline),
            'worst': worst_active_day(user_timeline),
            'average': average_for_active_days(user_timeline)
        }
        user_list.append(record)

    for key, value in node_count_dict.items():
        start_date, end_date = date_range(timelines[key])
        start_date = time.strftime('%d-%m-%Y', start_date.timetuple())
        end_date = time.strftime('%d-%m-%Y', end_date.timetuple())
        user_timeline = timelines[key]
        record = {
            'name': key,
            'ways': 0,
            'nodes': value,
            'timeline': interpolated_timeline(user_timeline),
            'start': start_date,
            'end': end_date,
            'activeDays': len(user_timeline),
            'best': best_active_day(user_timeline),
            'worst': worst_active_day(user_timeline),
            'average': average_for_active_days(user_timeline)
        }
        user_list.append(record)

    # Sort it
    sorted_user_list = sorted(
        user_list, key=lambda d: (
            -d['ways'],
            d['nodes'],
            d['name'],
            d['timeline'],
            d['start'],
            d['end'],
            d['activeDays'],
            d['best'],
            d['worst'],
            d['average']))
    return sorted_user_list

