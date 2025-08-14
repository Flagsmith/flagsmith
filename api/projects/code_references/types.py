from dataclasses import dataclass
from datetime import datetime


@dataclass
class CodeReference:
    scanned_at: datetime
    revision: str
    feature_name: str
    file_path: str
    line_number: int
    permalink: str


@dataclass
class FeatureFlagCodeReferences:
    first_scanned_at: datetime | None
    last_scanned_at: datetime | None
    code_references: list[CodeReference]
