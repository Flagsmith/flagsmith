import typing

from django.db.models import Prefetch
from softdelete.models import SoftDeleteManager  # type: ignore[import-untyped]

from environments.constants import IDENTITY_INTEGRATIONS_RELATION_NAMES
from features.models import FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureStateValue
from segments.models import Segment

if typing.TYPE_CHECKING:
    from environments.models import Environment


class EnvironmentManager(SoftDeleteManager):  # type: ignore[misc]
    def filter_for_document_builder(  # type: ignore[no-untyped-def]
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
                Prefetch(
                    "project__segments",
                    queryset=Segment.live_objects.all(),
                ),
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

    def get_for_cache(self, api_key: str) -> "Environment":
        select_related_args = (
            "project",
            "project__organisation",
            *IDENTITY_INTEGRATIONS_RELATION_NAMES,
        )
        base_qs = self.select_related(*select_related_args).defer("description")
        qs_for_embedded_api_key = base_qs.filter(api_key=api_key)
        qs_for_fk_api_key = base_qs.filter(api_keys__key=api_key)
        environment: Environment = qs_for_embedded_api_key.union(
            qs_for_fk_api_key
        ).get()
        return environment

    def get_queryset(self):  # type: ignore[no-untyped-def]
        return super().get_queryset().select_related("project", "project__organisation")

    def get_by_natural_key(self, api_key):  # type: ignore[no-untyped-def]
        return self.get(api_key=api_key)
