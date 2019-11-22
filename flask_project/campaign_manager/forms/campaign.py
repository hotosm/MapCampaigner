__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '10/05/17'

from flask_wtf import FlaskForm
from wtforms.fields import (
    DateField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    HiddenField,
    TextAreaField,
    RadioField,
    BooleanField
)
from wtforms.validators import InputRequired, Optional, ValidationError
from urllib.parse import urlparse
from campaign_manager.utilities import get_types
from campaign_manager.views import valid_map_list
from campaign_manager.models.survey import Survey


class ManagerSelectMultipleField(SelectMultipleField):
    def pre_validate(self, form):
        if self.data:
            return True


def validate_map(form, field):
    tile_layer = urlparse(field.data)
    valid_map = valid_map_list()
    if tile_layer.scheme != '' \
            and (tile_layer.netloc != '' or tile_layer.path != ''):
        if tile_layer.scheme != 'https' and field.data not in valid_map:
            raise ValidationError('Please input url using "https://"')
        elif field.data not in valid_map:
            raise ValidationError(
                'The url is invalid or is not supported, please input another '
                'url. e.g. https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png '
                'or leave blank to use default')


class CampaignForm(FlaskForm):
    name = StringField(
        u'Campaign name',
        validators=[InputRequired()],
        description='Name for the campaign',
        render_kw={'placeholder': 'Name of your project'}
    )
    description = TextAreaField(
        u'Campaign description',
        description='Description for the campaign',
        render_kw={'placeholder': 'Describe the type of features that ' +
                   'are beng collected and any other participation details.'}
    )
    campaign_status = RadioField(
        u'Campaign status',
        description='Status of the campaign',
        choices=[
            ('Start', 'Start'),
            ('Finish', 'Finish')
        ]
    )
    link_to_omk = BooleanField(
        u'Add button to integrate OpenMapKit'
    )
    start_date = DateField(
        u'Start date of campaign',
        validators=[InputRequired()],
        render_kw={'placeholder': 'Start Date', 'type': 'date'}
    )
    end_date = DateField(
        u'End date of campaign',
        validators=[InputRequired()],
        render_kw={'placeholder': 'End Date', 'type': 'date'}
    )
    campaign_managers = HiddenField(
        u'Project managers',
        validators=[InputRequired()])
    remote_projects = ManagerSelectMultipleField(
        u'Remote Projects'
    )
    types_options = SelectField(
        u'Types of campaign',
        choices=Survey.to_form(),
        validators=[Optional()]
    )
    types = HiddenField(u'Types that selected for this campaign')
    user_id = HiddenField(u'User id')
    uploader = HiddenField(u'Uploader for this campaign')
    geometry = HiddenField(
        u'Map geometry for this campaign',
        validators=[InputRequired()])
    map_type = StringField(
        u'Campaign Map',
        description='Campaign manager may change the map view',
        validators=[validate_map],
        render_kw={'placeholder': 'Add custom basemap tiles URL. ' +
                   'Use TMS scheme.'}
    )
    selected_functions = HiddenField(
        u'Selected Functions')
    submit = SubmitField(u'Submit')
