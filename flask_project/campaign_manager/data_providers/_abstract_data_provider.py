__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '17/05/17'

from abc import ABCMeta


class AbstractDataProvider(object):
    """
    Abstract class Data Provider.
    """
    __metaclass__ = ABCMeta

    def get_data(self, *args):
        """ Get data based on args
        """
        raise NotImplementedError()
