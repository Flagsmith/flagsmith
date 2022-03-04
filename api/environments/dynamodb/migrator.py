from django.db.models import Prefetch
from flag_engine.django_transform.document_builders import (
    build_identity_document,
)

from environments.models import Environment
from features.models import FeatureState
from features.multivariate.models import MultivariateFeatureStateValue

from .dynamodb_wrapper import DynamoIdentityWrapper
from .types import DynamoProjectMetadata, ProjectIdentityMigrationStatus


class IdentityMigrator:
    def __init__(self, project_id):
        self.project_metadata = DynamoProjectMetadata.get_or_new(project_id)

    @property
    def migration_status(self) -> ProjectIdentityMigrationStatus:
        if not self.project_metadata.migration_start_time:
            return ProjectIdentityMigrationStatus.MIGRATION_NOT_STARTED
        elif (
            self.project_metadata.migration_start_time
            and not self.project_metadata.migration_end_time
        ):
            return ProjectIdentityMigrationStatus.MIGRATION_IN_PROGRESS

        return ProjectIdentityMigrationStatus.MIGRATION_COMPLETED

    @property
    def is_migration_done(self) -> bool:
        migration_status = self.migration_status
        return migration_status == ProjectIdentityMigrationStatus.MIGRATION_COMPLETED

    @property
    def can_migrate(self) -> bool:
        migration_status = self.migration_status
        return migration_status == ProjectIdentityMigrationStatus.MIGRATION_NOT_STARTED

    def migrate(self):
        self.project_metadata.start_identity_migration()
        project_id = self.project_metadata.id
        identity_wrapper = DynamoIdentityWrapper()
        with identity_wrapper._table.batch_writer() as batch:
            for environment in Environment.objects.filter(project_id=project_id):
                for identity in environment.identities.all().prefetch_related(
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
                ):
                    identity_document = build_identity_document(identity)
                    batch.put_item(Item=identity_document)

        self.project_metadata.finish_identity_migration()
