from dataclasses import dataclass


@dataclass
class DynamoProjectMetadata:
    id: int
    is_migration_done: bool = False
