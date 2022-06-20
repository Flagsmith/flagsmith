from django.db.models import Manager


class ProjectManager(Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related("organisation")

    def get_by_natural_key(self, *args):
        name, organisation_id, created_date = args
        return self.get(
            name=name, organisation=organisation_id, created_date=created_date
        )
