import typing

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django_lifecycle import (
    AFTER_CREATE,
    BEFORE_SAVE,
    LifecycleModelMixin,
    hook,
)

from features.feature_states.models import AbstractBaseFeatureValueModel
from features.multivariate.managers import MultivariateFeatureStateValueManager

if typing.TYPE_CHECKING:
    from features.models import FeatureState


class MultivariateFeatureOption(LifecycleModelMixin, AbstractBaseFeatureValueModel):
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

    def natural_key(self):
        return (
            self.feature_id,
            self.type,
            self.string_value,
            self.integer_value,
            self.boolean_value,
        )


class MultivariateFeatureStateValue(LifecycleModelMixin, models.Model):
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

    objects = MultivariateFeatureStateValueManager()

    class Meta:
        unique_together = ("feature_state", "multivariate_feature_option")

    def natural_key(self):
        return self.feature_state_id, self.multivariate_feature_option_id

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
        )

        if persist:
            clone.save()

        return clone
