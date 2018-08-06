from datetime import datetime, date
from aws import S3Data


class Campaign(object):
    def __init__(self, key):
        self.key = key
        self.content = S3Data().fetch(
            'campaigns/{}/campaign.json'.format(key))

    def is_active(self):
        if len(self.content) == 0:
            return False
        start_datetime = datetime.strptime(
            self.content['start_date'],
            "%Y-%m-%d")
        end_datetime = datetime.strptime(
            self.content['end_date'],
            "%Y-%m-%d")

        status = False
        if start_datetime.date() <= date.today():
            if end_datetime.date() > date.today():
                status = True
        return status

    @staticmethod
    def all():
        return S3Data().list('campaigns')

    @staticmethod
    def active():
        return list(filter(
            lambda x: Campaign(x).is_active(), Campaign.all()))
