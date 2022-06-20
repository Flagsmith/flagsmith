from django.db.models import Manager


class TagManager(Manager):
    def get_by_natural_key(self, label, project):
        return self.get(project=project, label=label)
