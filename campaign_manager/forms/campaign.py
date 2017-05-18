__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '10/05/17'

import inspect

from flask_wtf import FlaskForm
from wtforms.fields import (
    DateField,
    SelectMultipleField,
    StringField,
    SubmitField
)
from wtforms.validators import DataRequired, Optional
from campaign_manager.settings import users
import campaign_manager.selected_functions as selected_functions


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
        u'Managers of campaign', choices=[(user, user) for user in users])
    selected_functions = SelectMultipleField(
        u'Functions for this campaign',
        choices=[
            (insights_function, insights_function)
            for insights_function in [
                m[0] for m in inspect.getmembers(
                    selected_functions, inspect.isclass
                )
                ]
            ]
    )
    submit = SubmitField(u'Submit')
