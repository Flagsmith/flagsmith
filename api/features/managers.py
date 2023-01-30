from __future__ import unicode_literals

from core.models import UUIDNaturalKeyManagerMixin
from ordered_model.models import OrderedModelManager
from softdelete.models import SoftDeleteManager


class FeatureSegmentManager(UUIDNaturalKeyManagerMixin, OrderedModelManager):
    pass


class FeatureManager(UUIDNaturalKeyManagerMixin, SoftDeleteManager):
    pass


class FeatureStateManager(UUIDNaturalKeyManagerMixin, SoftDeleteManager):
    pass


class FeatureStateValueManager(UUIDNaturalKeyManagerMixin, SoftDeleteManager):
    pass
