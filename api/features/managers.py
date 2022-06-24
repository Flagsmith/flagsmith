from core.models import UUIDNaturalKeyManagerMixin
from ordered_model.models import OrderedModelManager


class FeatureSegmentManager(UUIDNaturalKeyManagerMixin, OrderedModelManager):
    pass
