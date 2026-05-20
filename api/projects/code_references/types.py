from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict

from django.db.models import TextChoices

from projects.models import Project


class VCSProvider(TextChoices):
    GITHUB = "github", "GitHub"


class StoredCodeReference(TypedDict):
    file_path: str
    line_number: int


class SubmittedCodeReference(StoredCodeReference):
    feature_name: str


@dataclass
class CodeReference:
    feature_name: str
    file_path: str
    line_number: int
    permalink: str


@dataclass
class FeatureFlagCodeReferencesRepositorySummary:
    repository_url: str
    vcs_provider: VCSProvider
    revision: str
    last_successful_repository_scanned_at: datetime
    last_feature_found_at: datetime | None
    code_references: list[CodeReference]


@dataclass
class CodeReferencesRepositoryCount:
    repository_url: str
    count: int
    last_successful_repository_scanned_at: datetime
    last_feature_found_at: datetime | None


@dataclass
class FeatureFlagCodeReferencesScan:
    created_at: datetime
    repository_url: str
    vcs_provider: VCSProvider
    revision: str
    code_references: list[SubmittedCodeReference]
    project: Project
