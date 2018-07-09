from app_config import Config
from campaign_manager import campaign_manager


def inject_oauth_param():
    """Runs before the Template is rendered and injects Oauth param value.
    :return: function providing OAuth parameter.
    :rtype: dict"""
    def oauth_param(oauth_param):
        """Returns the OAuth parameter.
        :param oauth_param: Required secret paramter for the OSM OAuth.
        :type oauth_param: str
        :return: secret OAuth parameter.
        :rtype: str
        """
        context = dict(
            oauth_consumer_key=Config.OAUTH_CONSUMER_KEY,
            oauth_secret=Config.OAUTH_SECRET)
        return context[oauth_param]
    return dict(oauth_param=oauth_param)
