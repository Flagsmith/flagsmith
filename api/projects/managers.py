from core.models import AbstractBaseExportableModelManager
from softdelete.models import SoftDeleteManager


class ProjectManager(SoftDeleteManager, AbstractBaseExportableModelManager):
    def get_queryset(self):
        return super().get_queryset().select_related("organisation")
