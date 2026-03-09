from collections.abc import Iterator

from django.db.models import Prefetch

from edge_api.identities.events import send_migration_event
from environments.identities.models import Identity
from environments.models import Environment, EnvironmentAPIKey
from features.models import FeatureState
from features.multivariate.models import MultivariateFeatureStateValue
from projects.models import Project

from .types import DynamoProjectMetadata, ProjectIdentityMigrationStatus
from .wrappers import (
    DynamoEnvironmentAPIKeyWrapper,
    DynamoEnvironmentWrapper,
    DynamoIdentityWrapper,
)


class IdentityMigrator:
    @staticmethod
    def iter_identities_in_chunks(
        project_id: int, chunk_size: int = 2000
    ) -> Iterator[Identity]:
        """
        Yield identities in fixed-size chunks using keyset pagination.

        We don't use Django's built-in QuerySet.iterator() here because
        it uses server-side cursors (DECLARE/FETCH), which plan the
        entire result set upfront and can hit statement_timeout on
        large tables.

        Each chunk issues a WHERE pk > last_pk ORDER BY pk LIMIT N query,
        which is O(1) via pk index seek regardless of table size.
        """
        identities_qs = (
            Identity.objects.filter(environment__project__id=project_id)
            .select_related("environment")
            .prefetch_related(
                "identity_traits",
                Prefetch(
                    "identity_features",
                    queryset=FeatureState.objects.select_related(
                        "feature", "feature_state_value"
                    ),
                ),
                Prefetch(
                    "identity_features__multivariate_feature_state_values",
                    queryset=MultivariateFeatureStateValue.objects.select_related(
                        "multivariate_feature_option"
                    ),
                ),
            )
        )
        queryset = identities_qs.order_by("pk")
        last_pk = None

        while True:
            chunk_qs = (
                queryset.filter(pk__gt=last_pk) if last_pk is not None else queryset
            )
            chunk = list(chunk_qs[:chunk_size])
            if not chunk:
                break
            yield from chunk
            last_pk = chunk[-1].pk

    def __init__(self, project_id):  # type: ignore[no-untyped-def]
        self.project_metadata = DynamoProjectMetadata.get_or_new(project_id)

    @property
    def migration_status(self) -> ProjectIdentityMigrationStatus:
        return self.project_metadata.identity_migration_status

    @property
    def is_migration_done(self) -> bool:
        migration_status = self.migration_status
        return migration_status == ProjectIdentityMigrationStatus.MIGRATION_COMPLETED

    @property
    def can_migrate(self) -> bool:
        return self.migration_status in (
            ProjectIdentityMigrationStatus.MIGRATION_NOT_STARTED,
            ProjectIdentityMigrationStatus.MIGRATION_SCHEDULED,
        )

    def trigger_migration(self):  # type: ignore[no-untyped-def]
        # Note: since we mark the project as `migration in progress` before we start the migration,
        # there is a small chance for the project of being stuck in `migration in progress`
        # if the migration event is lost or the task fails.
        # Since the probability of this happening is low, we don't worry about it.
        send_migration_event(self.project_metadata.id)
        self.project_metadata.trigger_identity_migration()  # type: ignore[no-untyped-call]

    def migrate(self):  # type: ignore[no-untyped-def]
        self.project_metadata.start_identity_migration()  # type: ignore[no-untyped-call]

        project_id = self.project_metadata.id

        Project.objects.filter(id=project_id).update(enable_dynamo_db=True)
        environment_wrapper = DynamoEnvironmentWrapper()
        environments = Environment.objects.filter_for_document_builder(
            project_id=project_id
        )
        environment_wrapper.write_environments(environments)

        api_key_wrapper = DynamoEnvironmentAPIKeyWrapper()
        api_keys = EnvironmentAPIKey.objects.filter(environment__project_id=project_id)
        api_key_wrapper.write_api_keys(api_keys)

        identity_wrapper = DynamoIdentityWrapper(
            environment_wrapper=environment_wrapper
        )
        identity_wrapper.write_identities(self.iter_identities_in_chunks(project_id))  # type: ignore[no-untyped-call]
        self.project_metadata.finish_identity_migration()  # type: ignore[no-untyped-call]
