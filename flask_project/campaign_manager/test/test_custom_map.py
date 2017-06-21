# coding=utf-8
from unittest import TestCase, mock
from app import osm_app as app
from wtforms.validators import ValidationError
from campaign_manager.forms.campaign import validate_map, CampaignForm
from campaign_manager.views import find_attribution


class ValidateMapTestCase(TestCase):

    def setUp(self):
        """Constructor."""
        app.config['TESTING'] = True
        pass

    def tearDown(self):
        """Destructor."""
        pass

    def test_validate_map_using_http(self):
        input_map = 'http://somemap.png'
        input_form = mock.MagicMock(data=input_map)
        self.assertRaises(
            ValidationError, validate_map, CampaignForm, input_form)
        try:
            validate_map(CampaignForm, input_form)
        except ValidationError as error:
            self.assertEquals(
                error.args[0], 'Please input url using "https://"')

    def test_validate_map_using_invalid_url(self):
        input_map = 'https://somemap.png'
        input_form = mock.MagicMock(data=input_map)
        self.assertRaises(
            ValidationError, validate_map, CampaignForm, input_form)
        try:
            validate_map(CampaignForm, input_form)
        except ValidationError as error:
            self.assertEquals(
                error.args[0],
                'The url is invalid or is not supported, please input another '
                'url. e.g. https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png '
                'or leave blank to use default')

    def test_validate_map_using_valid_url(self):
        input_map = 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png'
        input_form = mock.MagicMock(data=input_map)
        response = validate_map(CampaignForm, input_form)
        self.assertIsNone(response)  # No error raised.


class FindAttributionTest(TestCase):
    """Test function to call the right attribution."""

    def test_find_attribute(self):
        input_map = 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png'
        expected_attribution = \
            '&copy; <a href="http://www.openstreetmap.org/copyright">' \
            'OpenStreetMap</a>, Tiles courtesy of ' \
            '<a href="http://hot.openstreetmap.org/" target="_blank">' \
            'Humanitarian OpenStreetMap Team</a>'
        attribution = find_attribution(input_map)
        self.assertEquals(attribution, expected_attribution)
