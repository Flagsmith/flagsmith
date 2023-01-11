from core.models import UUIDNaturalKeyManagerMixin
from ordered_model.models import OrderedModelManager
from softdelete.models import SoftDeleteManager


class FeatureSegmentManager(
    SoftDeleteManager, UUIDNaturalKeyManagerMixin, OrderedModelManager
):
    pass
