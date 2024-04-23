from django.db.models import Prefetch
from softdelete.models import SoftDeleteManager

from features.models import FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureStateValue


class EnvironmentManager(SoftDeleteManager):
    def filter_for_document_builder(
        self,
        *args,
        extra_select_related: list[str] | None = None,
        extra_prefetch_related: list[Prefetch | str] | None = None,
        **kwargs,
    ):
        return (
            super()
            .select_related(
                "project",
                "project__organisation",
                *extra_select_related or (),
            )
            .prefetch_related(
                "project__segments",
                "project__segments__rules",
                "project__segments__rules__rules",
                "project__segments__rules__conditions",
                "project__segments__rules__rules__conditions",
                "project__segments__rules__rules__rules",
                Prefetch(
                    "project__segments__feature_segments",
                    queryset=FeatureSegment.objects.select_related("segment"),
                ),
                Prefetch(
                    "project__segments__feature_segments__feature_states",
                    queryset=FeatureState.objects.select_related(
                        "feature", "feature_state_value", "environment"
                    ),
                ),
                Prefetch(
                    "project__segments__feature_segments__feature_states__multivariate_feature_state_values",
                    queryset=MultivariateFeatureStateValue.objects.select_related(
                        "multivariate_feature_option"
                    ),
                ),
                *extra_prefetch_related or (),
            )
            .filter(*args, **kwargs)
        )

    def get_queryset(self):
        return super().get_queryset().select_related("project", "project__organisation")

    def get_by_natural_key(self, api_key):
        return self.get(api_key=api_key)
