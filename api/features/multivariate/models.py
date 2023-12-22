import typing
import uuid

from core.models import (
    AbstractBaseExportableModel,
    abstract_base_auditable_model_factory,
)
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django_lifecycle import (
    AFTER_CREATE,
    AFTER_DELETE,
    BEFORE_SAVE,
    LifecycleModelMixin,
    hook,
)

from audit.related_object_type import RelatedObjectType
from features.feature_states.models import AbstractBaseFeatureValueModel
from features.feature_types import MULTIVARIATE, STANDARD

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from features.models import FeatureState
    from projects.models import Project


class MultivariateFeatureOption(
    LifecycleModelMixin,
    AbstractBaseFeatureValueModel,
    AbstractBaseExportableModel,
    abstract_base_auditable_model_factory(["uuid"]),
):
    """
    This class holds the *value* for a given multivariate feature
    option. This value is the same for every environment, but the
    percent allocation is set in MultivariateFeatureStateValue
    which varies per-environment.
    """

    history_record_class_path = (
        "features.multivariate.models.HistoricalMultivariateFeatureOption"
    )
    related_object_type = RelatedObjectType.FEATURE

    feature = models.ForeignKey(
        "features.Feature",
        on_delete=models.CASCADE,
        related_name="multivariate_options",
    )

    # This field is stored at the feature level but not used here - it is transferred
    # to the MultivariateFeatureStateValue on creation of a new option or when creating
    # a new environment.
    default_percentage_allocation = models.FloatField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    @hook(AFTER_CREATE)
    def create_multivariate_feature_state_values(self):
        for feature_state in self.feature.feature_states.filter(
            identity=None, feature_segment=None
        ):
            MultivariateFeatureStateValue.objects.create(
                feature_state=feature_state,
                multivariate_feature_option=self,
                percentage_allocation=self.default_percentage_allocation,
            )

    @hook(AFTER_CREATE)
    def make_feature_multivariate(self):
        # Handle the check on feature.type in the method itself to ensure this is
        # only performed after create. Using `when` and `is_not` means
        # LifecycleModel.__init__() queries for feature on every object init.
        if self.feature.type != MULTIVARIATE:
            self.feature.type = MULTIVARIATE
            self.feature.save()

    @hook(AFTER_DELETE)
    def make_feature_standard(self):
        if self.feature.multivariate_options.count() == 0:
            self.feature.type = STANDARD
            self.feature.save()

    def get_create_log_message(self, history_instance) -> typing.Optional[str]:
        return f"Multivariate option added to feature '{self.feature.name}'."

    def get_delete_log_message(self, history_instance) -> typing.Optional[str]:
        if not self.feature.deleted_at:
            return f"Multivariate option removed from feature '{self.feature.name}'."

    def get_audit_log_related_object_id(self, history_instance) -> int:
        return self.feature_id

    def _get_project(self) -> typing.Optional["Project"]:
        return self.feature.project


class MultivariateFeatureStateValue(
    LifecycleModelMixin,
    AbstractBaseExportableModel,
    abstract_base_auditable_model_factory(["uuid"]),
):
    history_record_class_path = (
        "features.multivariate.models.HistoricalMultivariateFeatureStateValue"
    )
    related_object_type = RelatedObjectType.FEATURE_STATE

    feature_state = models.ForeignKey(
        "features.FeatureState",
        on_delete=models.CASCADE,
        related_name="multivariate_feature_state_values",
    )
    multivariate_feature_option = models.ForeignKey(
        MultivariateFeatureOption, on_delete=models.CASCADE
    )

    percentage_allocation = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    class Meta:
        unique_together = ("feature_state", "multivariate_feature_option")

    @hook(BEFORE_SAVE)
    def validate_unique(self, exclude=None):
        """
        Override validate_unique method, so we can add the BEFORE_SAVE hook.
        """
        super(MultivariateFeatureStateValue, self).validate_unique(exclude=exclude)

    def clone(self, feature_state: "FeatureState", persist: bool = True):
        clone = MultivariateFeatureStateValue(
            feature_state=feature_state,
            multivariate_feature_option=self.multivariate_feature_option,
            percentage_allocation=self.percentage_allocation,
            uuid=uuid.uuid4(),
        )

        if persist:
            clone.save()

        return clone

    def get_update_log_message(self, history_instance) -> typing.Optional[str]:
        feature_state = self.feature_state
        feature = feature_state.feature

        if feature_state.identity_id:
            identifier = feature_state.identity.identifier
            return f"Multivariate value changed for feature '{feature.name}' and identity '{identifier}'."
        elif feature_state.feature_segment_id:
            segment = feature_state.feature_segment.segment
            return f"Multivariate value changed for feature '{feature.name}' and segment '{segment.name}'."

        return f"Multivariate value changed for feature '{feature.name}'."

    def get_audit_log_related_object_id(self, history_instance) -> int:
        if self.feature_state.belongs_to_uncommited_change_request:
            return None

        return self.feature_state.feature_id

    def _get_environment(self) -> typing.Optional["Environment"]:
        return self.feature_state.environment
