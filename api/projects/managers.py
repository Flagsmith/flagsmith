from core.models import AbstractBaseExportableModelManager
from softdelete.models import SoftDeleteManager  # type: ignore[import-untyped]


class ProjectManager(SoftDeleteManager, AbstractBaseExportableModelManager):  # type: ignore[misc]
    def get_queryset(self):  # type: ignore[no-untyped-def]
        return super().get_queryset().select_related("organisation")
