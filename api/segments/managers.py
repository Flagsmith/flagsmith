from django.db.models import F

from core.models import SoftDeleteExportableManager


class SegmentManager(SoftDeleteExportableManager):
    pass


class LiveSegmentManager(SoftDeleteExportableManager):
    def get_queryset(self):  # type: ignore[no-untyped-def]
        """
        Returns only the canonical segments, which will always be
        the highest version.
        """
        return super().get_queryset().filter(id=F("version_of"))
