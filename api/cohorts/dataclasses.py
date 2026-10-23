from dataclasses import dataclass


@dataclass
class CsvIdentifierExtraction:
    identifiers: list[str]
    empty_count: int
    duplicate_count: int
    too_long_count: int


@dataclass
class CohortCsvIgnoredRows:
    empty: int
    duplicates: int
    too_long: int


@dataclass
class CohortCsvSyncResult:
    version: int
    added: int
    removed: int
    unchanged: int
    ignored: CohortCsvIgnoredRows
