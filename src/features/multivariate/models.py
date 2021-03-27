from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django_lifecycle import LifecycleModelMixin, hook, AFTER_CREATE

from features.feature_states.models import AbstractBaseFeatureValueModel


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
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    @hook(AFTER_CREATE)
    def create_multivariate_feature_state_values(self):
        for feature_state in self.feature.feature_states.all():
            MultivariateFeatureStateValue.objects.create(
                feature_state=feature_state,
                multivariate_feature_option=self,
                percentage_allocation=self.default_percentage_allocation,
            )


class MultivariateFeatureStateValue(models.Model):
    feature_state = models.ForeignKey(
        "features.FeatureState",
        on_delete=models.CASCADE,
        related_name="multivariate_feature_state_values",
    )
    multivariate_feature_option = models.ForeignKey(
        MultivariateFeatureOption, on_delete=models.CASCADE
    )

    percentage_allocation = models.FloatField(
        blank=False,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
