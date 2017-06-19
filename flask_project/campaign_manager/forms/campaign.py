__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '10/05/17'

from flask_wtf import FlaskForm
from wtforms.fields import (
    DateField,
    SelectMultipleField,
    StringField,
    SubmitField,
    HiddenField,
    TextAreaField,
    RadioField
)
from wtforms.validators import DataRequired, Optional, ValidationError
from urllib.parse import urlparse
from campaign_manager.utilities import get_osm_user, get_tags


class ManagerSelectMultipleField(SelectMultipleField):

    def pre_validate(self, form):
        if self.data:
            return True


def validate_map(form, field):
    tile_layer = urlparse(field.data)
    valid_map_list = (
        '{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        '{s}.tile.openstreetmap.de/tiles/osmde/{z}/{x}/{y}.png',
        '{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png',
        '{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
        '{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        '{s}.tile.openstreetmap.se/hydda/full/{z}/{x}/{y}.png',
        '{s}.tile.openstreetmap.se/hydda/base/{z}/{x}/{y}.png',
        'server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/'
        'MapServer/tile/{z}/{y}/{x}',
        'server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/'
        'MapServer/tile/{z}/{y}/{x}',
        'server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/'
        'MapServer/tile/{z}/{y}/{x}',
        'maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png',
        'maps.wikimedia.org/osm/{z}/{x}/{y}.png',
        'cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png',
    )
    map_source = '%s%s' % (tile_layer.netloc, tile_layer.path)
    if tile_layer.scheme != '' \
            and (tile_layer.netloc != '' or tile_layer.path != ''):
        if tile_layer.scheme != 'https':
            raise ValidationError('Please input url using "https://"')
        elif map_source not in valid_map_list:
            raise ValidationError(
                'The url is invalid or is not supported, please input another '
                'url. e.g. https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png '
                'or leave blank to use default')


class CampaignForm(FlaskForm):
    name = StringField(
        u'Campaign name',
        validators=[DataRequired('Campaign name is needed')],
        description='Name for the campaign'
    )
    description = TextAreaField(
        u'Campaign description',
        description='Description for the campaign'
    )
    campaign_status = RadioField(
        u'Campaign status',
        description='Status of the campaign',
        choices=[
            ('Start', 'Start'),
            ('Finish', 'Finish')
        ]
    )

    start_date = DateField(
            u'Start date of campaign')
    end_date = DateField(
            u'End date of campaign')

    campaign_managers = ManagerSelectMultipleField(
        u'Managers of campaign',
        validators=[DataRequired('Campaign manager is needed')])
    tags = SelectMultipleField(
        u'Tags of campaign',
        choices=[(tag, tag) for tag in get_tags()])
    uploader = HiddenField(u'Uploader for this campaign')
    geometry = HiddenField(
        u'Map geometry for this campaign',
        validators=[DataRequired('Geometry is needed')])
    map_type = StringField(
        u'Campaign Map',
        description='Campaign manager may change the map view',
        validators=[validate_map])
    selected_functions = HiddenField(
        u'Selected Functions')
    submit = SubmitField(u'Submit')
