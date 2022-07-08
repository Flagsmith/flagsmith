from django.db.models import Prefetch

from edge_api.identities.events import send_migration_event
from environments.identities.models import Identity
from environments.models import Environment
from features.models import FeatureState
from features.multivariate.models import MultivariateFeatureStateValue
from projects.models import Project
from util.queryset import iterator_with_prefetch

from .dynamodb_wrapper import DynamoEnvironmentWrapper, DynamoIdentityWrapper
from .types import DynamoProjectMetadata, ProjectIdentityMigrationStatus


class IdentityMigrator:
    def __init__(self, project_id):
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

    def trigger_migration(self):
        # Note: since we mark the project as `migration in progress` before we start the migration,
        # there is a small chance for the project of being stuck in `migration in progress`
        # if the migration event is lost or the task fails.
        # Since the probability of this happening is low, we don't worry about it.
        send_migration_event(self.project_metadata.id)
        self.project_metadata.trigger_identity_migration()

    def migrate(self):
        self.project_metadata.start_identity_migration()

        project_id = self.project_metadata.id

        Project.objects.filter(id=project_id).update(enable_dynamo_db=True)
        environment_wrapper = DynamoEnvironmentWrapper()
        environments = Environment.objects.filter_for_document_builder(
            project_id=project_id
        )
        environment_wrapper.write_environments(environments)

        identity_wrapper = DynamoIdentityWrapper()
        identities = (
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
        identity_wrapper.write_identities(iterator_with_prefetch(identities))
        self.project_metadata.finish_identity_migration()
