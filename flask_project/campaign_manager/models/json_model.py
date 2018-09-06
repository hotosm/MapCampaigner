__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '10/05/17'

from campaign_manager.models.version import Version


class JsonModel(Version):
    """
    Model that use json.
    """
    json_path = ''

    def parse_json_file(self):
        return NotImplemented

    def get_attributes(self):
        """ Get attributes of json model
        :return: attributes
        :rtype: list
        """
        return [
            attr for attr in dir(self)
            if not callable(getattr(self, attr)) and not attr.startswith("_")
            ]

    def to_dict(self):
        """ Return json model as dictionary.
        :return: dict
        """
        dict = {}
        for attribute in self.get_attributes():
            dict[attribute] = getattr(self, attribute)
        dict.pop('json_path')
        dict.pop('geojson_path')
        return dict

    @staticmethod
    class CorruptedFile(Exception):
        def __init__(self):
            self.message = "Json file for this model is corrupted"
            super(JsonModel.CorruptedFile, self).__init__(self.message)

    @staticmethod
    class RequiredAttributeMissed(Exception):
        def __init__(self, attribute):
            self.message = "%s is missed" % attribute
            super(JsonModel.RequiredAttributeMissed,
                  self).__init__(self.message)
