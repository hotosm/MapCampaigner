__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '10/05/17'

from flask_wtf import FlaskForm
from wtforms.fields import (
    DateField,
    SelectMultipleField,
    StringField,
    SubmitField,
    HiddenField
)
from wtforms.validators import DataRequired, Optional
from campaign_manager.utilities import get_osm_user


class CampaignForm(FlaskForm):
    name = StringField(
        u'Campaign name',
        validators=[DataRequired('Campaign name is needed')]
    )
    campaign_status = StringField(u'Campaign status')
    coverage = StringField(u'Coverage')
    start_date = DateField(u'Start date of campaign')
    end_date = DateField(u'End date of campaign', validators=[Optional()])

    campaign_managers = SelectMultipleField(
        u'Managers of campaign',
        choices=[(user, user) for user in get_osm_user()])
    uploader = HiddenField(u'Uploader for this campaign')
    geometry = HiddenField(
        u'Map geometry for this campaign',
        validators=[DataRequired('Geometry is needed')])
    selected_functions = HiddenField(
        u'Selected Functions')
    submit = SubmitField(u'Submit')
