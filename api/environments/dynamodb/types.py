import enum
from dataclasses import asdict, dataclass
from datetime import datetime

import boto3
from django.conf import settings
from flag_engine.features.models import FeatureStateModel
from pydantic import BaseModel

project_metadata_table = None

if settings.PROJECT_METADATA_TABLE_NAME_DYNAMO:
    project_metadata_table = boto3.resource("dynamodb").Table(
        settings.PROJECT_METADATA_TABLE_NAME_DYNAMO
    )


class ProjectIdentityMigrationStatus(enum.Enum):
    MIGRATION_SCHEDULED = "MIGRATION_SCHEDULED"
    MIGRATION_COMPLETED = "MIGRATION_COMPLETED"
    MIGRATION_IN_PROGRESS = "MIGRATION_IN_PROGRESS"
    MIGRATION_NOT_STARTED = "MIGRATION_NOT_STARTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class DynamoProjectMetadata:
    """Internal class used by `IdentityMigrator` to store identity migration state"""

    id: int
    migration_start_time: str = None
    migration_end_time: str = None
    triggered_at: str = None

    @classmethod
    def get_or_new(cls, project_id: int) -> "DynamoProjectMetadata":
        document = project_metadata_table.get_item(Key={"id": project_id}).get("Item")
        if document:
            return cls(**document)
        return cls(id=project_id)

    @property
    def identity_migration_status(self) -> ProjectIdentityMigrationStatus:
        if not self.migration_start_time:
            return (
                ProjectIdentityMigrationStatus.MIGRATION_SCHEDULED
                if self.triggered_at
                else ProjectIdentityMigrationStatus.MIGRATION_NOT_STARTED
            )
        elif self.migration_start_time and not self.migration_end_time:
            return ProjectIdentityMigrationStatus.MIGRATION_IN_PROGRESS
        return ProjectIdentityMigrationStatus.MIGRATION_COMPLETED

    def trigger_identity_migration(self):
        if self.triggered_at:
            raise AttributeError("Migration has already been triggered.")
        self.triggered_at = datetime.now().isoformat()
        self._save()

    def start_identity_migration(self):
        if self.migration_start_time:
            raise AttributeError("Migration has already been started.")
        self.migration_start_time = datetime.now().isoformat()
        self._save()

    def finish_identity_migration(self):
        if self.migration_end_time:
            raise AttributeError("Migration has already been finished.")
        self.migration_end_time = datetime.now().isoformat()
        self._save()

    def _save(self):
        return project_metadata_table.put_item(Item=asdict(self))

    def delete(self):
        if project_metadata_table:
            project_metadata_table.delete_item(Key={"id": self.id})


class IdentityOverrideV2(BaseModel):
    environment_id: str
    document_key: str
    environment_api_key: str
    identifier: str
    identity_uuid: str
    feature_state: FeatureStateModel


@dataclass
class IdentityOverridesV2Changeset:
    to_delete: list[IdentityOverrideV2]
    to_put: list[IdentityOverrideV2]
