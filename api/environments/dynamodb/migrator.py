from django.db.models import Prefetch
from flag_engine.django_transform.document_builders import (
    build_identity_document,
)

from environments.identities.models import Identity
from features.models import FeatureState
from features.multivariate.models import MultivariateFeatureStateValue

from .dynamodb_wrapper import DynamoIdentityWrapper
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
        migration_status = self.migration_status
        return migration_status == ProjectIdentityMigrationStatus.MIGRATION_NOT_STARTED

    def migrate(self):
        self.project_metadata.start_identity_migration()
        project_id = self.project_metadata.id
        identity_wrapper = DynamoIdentityWrapper()
        identities = Identity.objects.filter(
            environment__project__id=project_id
        ).prefetch_related(
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
        identity_wrapper.write_identities(identities)
        self.project_metadata.finish_identity_migration()
