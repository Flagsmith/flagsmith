from __future__ import annotations

import typing
from functools import lru_cache

import boto3
import structlog
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from experimentation.dataclasses import IngestionInfrastructure

if typing.TYPE_CHECKING:
    from typing import Any

logger = structlog.get_logger("experimentation")

AWS_REGION = "eu-west-2"
STREAM_NAME_PREFIX = "events-ingestion-org-"
# Buckets are created in the account regional namespace, so the name only has
# to be unique within our account and must follow the
# {prefix}-{account_id}-{region}-an convention.
BUCKET_NAME_PREFIX = "flagsmith-events-lake-org-"
BUCKET_NAMESPACE_HEADER = "x-amz-bucket-namespace"

# S3 object keys are namespaced per environment via Firehose dynamic
# partitioning on each record's environment_key field.
EVENTS_PREFIX = (
    "events/env_key=!{partitionKeyFromQuery:env_key}/"
    "year=!{timestamp:yyyy}/month=!{timestamp:MM}/"
    "day=!{timestamp:dd}/hour=!{timestamp:HH}/"
)
ERRORS_PREFIX = (
    "errors/!{firehose:error-output-type}/"
    "year=!{timestamp:yyyy}/month=!{timestamp:MM}/"
    "day=!{timestamp:dd}/hour=!{timestamp:HH}/"
)

# Firehose requires buffers of at least 64 MiB when dynamic partitioning is
# enabled.
BUFFERING_SIZE_MB = 64
BUFFERING_INTERVAL_SECONDS = 300
DYNAMIC_PARTITIONING_RETRY_SECONDS = 300
OBJECT_EXPIRATION_DAYS = 30

# Cost-allocation tag applied to per-organisation resources so AWS billing can
# be attributed per organisation.
ORGANISATION_TAG_KEY = "organisation_id"


def _add_account_regional_namespace_header(
    params: dict[str, Any],
    **kwargs: Any,
) -> None:
    params["headers"][BUCKET_NAMESPACE_HEADER] = "account-regional"


@lru_cache(maxsize=1)
def _get_s3_client() -> "Any":
    # The pinned boto3 version predates the CreateBucket BucketNamespace
    # parameter, so the corresponding header is injected directly.
    client = boto3.client("s3", region_name=AWS_REGION)
    client.meta.events.register(
        "before-call.s3.CreateBucket",
        _add_account_regional_namespace_header,
    )
    return client


@lru_cache(maxsize=1)
def _get_firehose_client() -> "Any":
    return boto3.client("firehose", region_name=AWS_REGION)


@lru_cache(maxsize=1)
def _get_account_id() -> str:
    sts = boto3.client("sts", region_name=AWS_REGION)
    return sts.get_caller_identity()["Account"]  # type: ignore[no-any-return]


def get_bucket_name(organisation_id: int) -> str:
    return f"{BUCKET_NAME_PREFIX}{organisation_id}-{_get_account_id()}-{AWS_REGION}-an"


def get_stream_name(organisation_id: int) -> str:
    return f"{STREAM_NAME_PREFIX}{organisation_id}"


def _create_events_bucket(bucket_name: str, *, organisation_id: int) -> None:
    s3 = _get_s3_client()
    s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
    )
    logger.info(
        "ingestion_infra.bucket_created",
        organisation__id=organisation_id,
        bucket__name=bucket_name,
    )
    s3.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )
    s3.put_bucket_lifecycle_configuration(
        Bucket=bucket_name,
        LifecycleConfiguration={
            "Rules": [
                {
                    "ID": "expire-objects",
                    "Filter": {"Prefix": ""},
                    "Status": "Enabled",
                    "Expiration": {"Days": OBJECT_EXPIRATION_DAYS},
                }
            ]
        },
    )
    s3.put_bucket_tagging(
        Bucket=bucket_name,
        Tagging={
            "TagSet": [{"Key": ORGANISATION_TAG_KEY, "Value": str(organisation_id)}]
        },
    )


def _expected_destination_configuration(bucket_name: str) -> dict[str, Any]:
    return {
        "RoleARN": settings.INGESTION_FIREHOSE_DELIVERY_ROLE_ARN,
        "BucketARN": f"arn:aws:s3:::{bucket_name}",
        "Prefix": EVENTS_PREFIX,
        "ErrorOutputPrefix": ERRORS_PREFIX,
        "BufferingHints": {
            "SizeInMBs": BUFFERING_SIZE_MB,
            "IntervalInSeconds": BUFFERING_INTERVAL_SECONDS,
        },
        "CompressionFormat": "GZIP",
        "DynamicPartitioningConfiguration": {
            "Enabled": True,
            "RetryOptions": {"DurationInSeconds": DYNAMIC_PARTITIONING_RETRY_SECONDS},
        },
        "ProcessingConfiguration": {
            "Enabled": True,
            "Processors": [
                {
                    "Type": "MetadataExtraction",
                    "Parameters": [
                        {
                            "ParameterName": "MetadataExtractionQuery",
                            "ParameterValue": "{env_key:.environment_key}",
                        },
                        {
                            "ParameterName": "JsonParsingEngine",
                            "ParameterValue": "JQ-1.6",
                        },
                    ],
                },
                {
                    "Type": "AppendDelimiterToRecord",
                    "Parameters": [
                        {"ParameterName": "Delimiter", "ParameterValue": "\\n"},
                    ],
                },
            ],
        },
    }


def _create_delivery_stream(
    stream_name: str,
    *,
    bucket_name: str,
    organisation_id: int,
) -> None:
    _get_firehose_client().create_delivery_stream(
        DeliveryStreamName=stream_name,
        DeliveryStreamType="DirectPut",
        ExtendedS3DestinationConfiguration=_expected_destination_configuration(
            bucket_name
        ),
        Tags=[{"Key": ORGANISATION_TAG_KEY, "Value": str(organisation_id)}],
    )
    logger.info(
        "ingestion_infra.stream_created",
        organisation__id=organisation_id,
        stream__name=stream_name,
        bucket__name=bucket_name,
    )


def provision_ingestion_infrastructure(
    organisation_id: int,
) -> IngestionInfrastructure:
    if not settings.INGESTION_FIREHOSE_DELIVERY_ROLE_ARN:
        raise ImproperlyConfigured("INGESTION_FIREHOSE_DELIVERY_ROLE_ARN is not set")
    bucket_name = get_bucket_name(organisation_id)
    stream_name = get_stream_name(organisation_id)

    _create_events_bucket(bucket_name, organisation_id=organisation_id)
    _create_delivery_stream(
        stream_name,
        bucket_name=bucket_name,
        organisation_id=organisation_id,
    )
    return IngestionInfrastructure(bucket_name=bucket_name, stream_name=stream_name)
