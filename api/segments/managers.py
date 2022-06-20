from django.db.models import Manager


class SegmentManager(Manager):
    def get_by_natural_key(self, *args):
        name, project = args
        return self.get(name=name, project=project)
