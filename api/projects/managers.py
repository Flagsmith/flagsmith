from core.models import AbstractBaseExportableModelManager


class ProjectManager(AbstractBaseExportableModelManager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related("organisation")
