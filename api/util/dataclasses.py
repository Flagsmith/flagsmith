from dataclasses import dataclass

from util.mappers.types import Document


@dataclass
class CompressedEnvironmentDocument:
    """Result of compressing an environment document for DynamoDB."""

    document: Document
    compressed_size_bytes: int
    compression_ratio: float
