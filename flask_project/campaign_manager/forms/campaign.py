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
from wtforms.validators import DataRequired, Optional
from campaign_manager.utilities import get_osm_user, get_tags


class ManagerSelectMultipleField(SelectMultipleField):

    def pre_validate(self, form):
        if self.data:
            return True


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
    selected_functions = HiddenField(
        u'Selected Functions')
    submit = SubmitField(u'Submit')
