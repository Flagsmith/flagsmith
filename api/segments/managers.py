from core.models import SoftDeleteManager, UUIDNaturalKeyManagerMixin
from django.db.models import F


class SegmentManager(UUIDNaturalKeyManagerMixin, SoftDeleteManager):
    pass


class LiveSegmentManager(UUIDNaturalKeyManagerMixin, SoftDeleteManager):
    def get_queryset(self):
        """
        Returns only the canonical segments, which will always be
        the highest version.
        """
        return super().get_queryset().filter(id=F("version_of"))
