import json
from aws import S3Data
import xml.sax
import time
from datetime import date, timedelta


def save_data(uuid, type_id, data):
    with open('/tmp/data.json', 'w') as file:
        json.dump(data, file)

    data_path = build_render_data_path(
        campaign_path=campaign_path(uuid),
        type_id=type_id)

    with open('/tmp/data.json', 'rb') as data:
        S3Data().upload_file(
            key=data_path,
            body=data)


def build_render_data_path(campaign_path, type_id):
    return '/'.join([
        '{campaign_path}',
        'render/{type_id}',
        'mapper_engagement.json']).format(
            campaign_path=campaign_path,
            type_id=type_id)


def fetch_type(seeked_feature, functions):
    return list(dict(filter(lambda function:
        is_function_and_feature(
            function_name=function[1]['function'],
            feature=function[1]['feature'],
            seeked_feature=seeked_feature),
        functions.items())).values())[0]['type']


def is_function_and_feature(function_name, feature, seeked_feature):
    return \
        function_name == 'MapperEngagement' \
        and \
        feature == seeked_feature


def build_raw_data_overpass_path(campaign_path, type_id):
    return '/'.join([
        '{campaign_path}',
        'overpass',
        '{type_id}.xml']).format(
            campaign_path=campaign_path,
            type_id=type_id)


def download_overpass_file(uuid, type_id):
    key = build_raw_data_overpass_path(
        campaign_path=campaign_path(uuid),
        type_id=type_id)

    S3Data().download_file(
        key=key,
        type_id=type_id,
        destination='/tmp')


def campaign_path(uuid):
    return '/'.join([
        'campaigns',
        '{uuid}']).format(
            uuid=uuid)

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

def date_range(timeline):
    """Given a timeline, determine the start and end dates.

    The timeline may be sparse (containing fewer entries than all the dates
    between the min and max dates) and since it is a dict,
    the dates may be in any order.

    :param timeline: A dictionary of non-sequential dates (in YYYY-MM-DD) as
    keys and values (representing ways collected on that day).
    :type timeline: dict

    :returns: A tuple containing two dates:
        * start_date - a date object representing the earliest date in the
            time line.
        * end_date - a date object representing the newest date in the time
            line.
    :rtype: (date, date)

    """
    start_date = None
    end_date = None
    for next_date in timeline.keys():
        year, month, day = next_date.split('-')
        message = 'Date: %s' % next_date
        timeline_date = date(int(year), int(month), int(day))
        if start_date is None:
            start_date = timeline_date
        if end_date is None:
            end_date = timeline_date
        if timeline_date < start_date:
            start_date = timeline_date
        if timeline_date > end_date:
            end_date = timeline_date
    return start_date, end_date

def interpolated_timeline(timeline):
    """Interpolate a timeline given a sparse timeline.

    A sparse timelines is a sequence of dates containing no days of zero
    activity. An interpolated timeline is a sequence of dates where there is
    an entry per day in the date range regardless of whether there was any
    activity or not.

    :param timeline: A dictionary of non-sequential dates (in YYYY-MM-DD) as
        keys and values (representing ways collected on that day).
    :type timeline: dict

    :returns:  An interpolated list where each date in the original input
        date is present, and all days where no total was provided are added
        to include that day.
    :rtype: list

    Given an input looking like this::

        {
            {u'2012-09-24': 1},
            {u'2012-09-21': 10},
            {u'2012-09-25': 5},
        }

    The returned list will be in the form::

        [
            [Date(2012,09,21), 10],
            [Date(2012,09,22), 0],
            [Date(2012,09,23), 0],
            [Date(2012,09,24), 1],
            [Date(2012,09,25), 5],
        ]
    """
    # Work out the earliest and latest day
    start_date, end_date = date_range(timeline)
    # Loop through them, adding an entry for each day
    time_line = '['
    for current_date in date_range_iterator(start_date, end_date):
        date_string = time.strftime('%Y-%m-%d', current_date.timetuple())
        if date_string in timeline:
            value = timeline[date_string]
        else:
            value = 0
        if value == 0:
            continue
        if time_line != '[':
            time_line += ','
        time_line += '["%s",%i]' % (date_string, value)
    time_line += ']'
    return time_line

def date_range_iterator(start_date, end_date):
    """Given two dates return a collection of dates between start and end.

    :param start_date: Date representing the start date.
    :type start_date: date

    :param end_date: Date representing the end date.
    :type end_date: date

    :returns: Iterable collection yielding dates.
    :rtype: iterable
    """
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def best_active_day(timeline):
    """Compute the best activity for a single active day in a sparse timeline.

    :param timeline: A dictionary of non-sequential dates (in YYYY-MM-DD) as
        keys and values (representing ways collected on that day).
    :type timeline: dict

    :returns: Number of entities captured for the user's best day.
    :rtype: int
    """
    best = 0
    for value in list(timeline.values()):
        if value > best:
            best = value
    return best


def worst_active_day(timeline):
    """Compute the worst activity for a single active day in a sparse timeline.

    :param timeline: A dictionary of non-sequential dates (in YYYY-MM-DD) as
        keys and values (representing ways collected on that day).
    :type timeline: dict

    :returns: Number of entities captured for the user's worst day.
    :rtype: int
    """
    if len(timeline) < 1:
        return 0
    worst = list(timeline.values())[0]
    for value in list(timeline.values()):
        if value == 0:  # should never be but just in case
            continue
        if value < worst:
            worst = value
    return worst

def average_for_active_days(timeline):
    """Compute the average activity per active day in a sparse timeline.

    :param timeline: A dictionary of non-sequential dates (in YYYY-MM-DD) as
        keys and values (representing ways collected on that day).
    :type timeline: dict

    :returns: Number of entities captured per day rounded to the nearest int.
    :rtype: int
    """
    count = 0
    total = 0
    for value in list(timeline.values()):
        if value > 0:
            count += 1
            total += value
    # Python 3 seems to automagically turn integer maths into float if needed
    average = int(total / count)
    return average

