import enum
from dataclasses import asdict, dataclass
from datetime import datetime

import boto3
from django.conf import settings

project_metadata_table = None

if settings.PROJECT_METADATA_TABLE_NAME_DYNAMO:
    project_metadata_table = boto3.resource("dynamodb").Table(
        settings.PROJECT_METADATA_TABLE_NAME_DYNAMO
    )


class ProjectIdentityMigrationStatus(enum.Enum):
    MIGRATION_COMPLETED = "MIGRATION_COMPLETED"
    MIGRATION_IN_PROGRESS = "MIGRATION_IN_PROGRESS"
    MIGRATION_NOT_STARTED = "MIGRATION_NOT_STARTED"


@dataclass
class DynamoProjectMetadata:
    """Internal class used by `DynamoIdentityWrapper` to track wether Identity
    data(for a given project) has been migrated or not"""

    id: int
    identity_migration_status: str = (
        ProjectIdentityMigrationStatus.MIGRATION_NOT_STARTED.name
    )
    migration_start_time: datetime = None

    @classmethod
    def get_or_new(cls, project_id: int) -> "DynamoProjectMetadata":
        document = project_metadata_table.get_item(Key={"id": project_id}).get("Item")
        if document:
            return cls(**document)
        return cls(id=project_id)

    def start_identity_migration(self):
        self.migration_start_time = datetime.now()
        self.identity_migration_status = (
            ProjectIdentityMigrationStatus.MIGRATION_IN_PROGRESS.name
        )
        self._save()

    def finish_identity_migration(self):
        self.identity_migration_status = (
            ProjectIdentityMigrationStatus.MIGRATION_COMPLETED.name
        )
        self._save()

    def _save(self):
        return project_metadata_table.put_item(Item=asdict(self))
