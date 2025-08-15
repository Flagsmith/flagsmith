from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict

from django.db.models import TextChoices


class VCSProvider(TextChoices):
    GITHUB = "github", "GitHub"


class JSONCodeReference(TypedDict):
    feature_name: str
    file_path: str
    line_number: int


@dataclass
class CodeReference:
    scanned_at: datetime
    vcs_provider: VCSProvider
    repository_url: str
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


@dataclass
class CodeReferencesRepositoryCount:
    repository_url: str
    count: int
