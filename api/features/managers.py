from __future__ import unicode_literals

import typing

from django.db.models import Q, QuerySet
from django.utils import timezone
from ordered_model.models import OrderedModelManager  # type: ignore[import-untyped]
from softdelete.models import SoftDeleteManager  # type: ignore[import-untyped]

from core.models import UUIDNaturalKeyManagerMixin
from features.versioning.models import EnvironmentFeatureVersion

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from features.models import FeatureState


class FeatureSegmentManager(UUIDNaturalKeyManagerMixin, OrderedModelManager):  # type: ignore[misc]
    pass


class FeatureManager(UUIDNaturalKeyManagerMixin, SoftDeleteManager):  # type: ignore[misc]
    pass


class FeatureStateManager(UUIDNaturalKeyManagerMixin, SoftDeleteManager):  # type: ignore[misc]
    def get_live_feature_states(  # type: ignore[no-untyped-def]
        self,
        environment: "Environment",
        additional_filters: Q = None,  # type: ignore[assignment]
        **kwargs,
    ) -> QuerySet["FeatureState"]:
        # TODO: replace additional_filters with just using kwargs in calling locations

        now = timezone.now()

        qs_filter = Q(environment=environment, deleted_at__isnull=True)
        if environment.use_v2_feature_versioning:
            latest_versions = (
                EnvironmentFeatureVersion.objects.get_latest_versions_by_environment_id(
                    environment.id
                )
            )
            latest_version_uuids = [efv.uuid for efv in latest_versions]

            # Note that since identity overrides aren't part of the versioning system,
            # we need to make sure we also return them here. We can still then subsequently
            # filter them out with the `additional_filters` if needed.
            qs_filter &= Q(
                Q(environment_feature_version__uuid__in=latest_version_uuids)
                | Q(identity__isnull=False)
            )
        else:
            qs_filter &= Q(
                live_from__isnull=False,
                live_from__lte=now,
                version__isnull=False,
            )

        if additional_filters:
            qs_filter &= additional_filters

        return self.filter(qs_filter, **kwargs)  # type: ignore[no-any-return]


class FeatureStateValueManager(UUIDNaturalKeyManagerMixin, SoftDeleteManager):  # type: ignore[misc]
    pass
