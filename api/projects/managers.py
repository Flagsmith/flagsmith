from django.db.models import Manager


class ProjectManager(Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related("organisation")
