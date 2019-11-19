from campaign_manager.aws import S3Data
import yaml, os
from glob import glob


class Survey():

    def __init__(self, file):
        self.data = self.read_yaml_file(file)
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
        path = os.path.join(
            os.getcwd(),
            'flask_project/campaign_manager/feature_templates',
            '*.yml'
        )
        files = glob(path)

        files = [os.path.splitext(os.path.split(f)[-1])[0] for f in files]

        return files

    @staticmethod
    def find_by_name(survey_name):
        return Survey(survey_name)

    @staticmethod
    def to_form():
        return [(survey, survey) for survey in Survey.all()]

    @staticmethod
    def read_yaml_file(filename):
        with open(filename, 'r') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
