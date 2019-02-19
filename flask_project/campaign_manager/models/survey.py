from campaign_manager.aws import S3Data


class Survey():

    def __init__(self, survey_name):
        self.data = S3Data().fetch('surveys/{}'.format(survey_name))
        self.do_tags()
        self.feature = self.feature()

    def do_tags(self):
        if len(self.data) > 0:
            tags = {}
            if 'tags' in self.data:
                for tag in self.data['tags']:
                    if isinstance(tag, str):
                        tags[tag] = []
                    else:
                        tags.update(tag)
            self.data['tags'] = tags

    def feature(self):
        if len(self.data) > 0:
            return self.data['feature']
        else:
            None

    @staticmethod
    def all():
        surveys = S3Data().list('surveys')

        # Remove modified value when listing surveys.
        surveys = [s['uuid'] for s in surveys]

        return surveys

    @staticmethod
    def find_by_name(survey_name):
        return Survey(survey_name)

    @staticmethod
    def to_form():
        return [(survey, survey) for survey in Survey.all()]
