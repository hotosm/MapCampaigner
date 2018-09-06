__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '13/06/17'

from app_config import Config
from campaign_manager.data_providers._abstract_osmcha_provider import (
    AbstractOsmchaProvider
)


class OsmchaFeaturesProvider(AbstractOsmchaProvider):
    """Data Changeset from osmcha"""

    def get_api_url(self):
        """ Return url of osmcha

        :return: url
        :rtype:str
        """
        return Config().OSMCHA_API + 'features/'
