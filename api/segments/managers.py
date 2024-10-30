from core.models import SoftDeleteExportableManager
from django.db.models import F


class SegmentManager(SoftDeleteExportableManager):
    def get_queryset(self):
        """
        Returns only the canonical segments, which will always be
        the highest version.
        """
        return super().get_queryset().filter(id=F("version_of"))
