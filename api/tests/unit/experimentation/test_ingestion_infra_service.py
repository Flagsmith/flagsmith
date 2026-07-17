from collections.abc import Iterator
from typing import Any

import boto3
import pytest
from botocore.exceptions import ClientError
from django.core.exceptions import ImproperlyConfigured
from moto import mock_firehose, mock_s3  # type: ignore[import-untyped]
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from experimentation import ingestion_infra_service
from experimentation.dataclasses import IngestionInfrastructure

DELIVERY_ROLE_ARN = "arn:aws:iam::123456789012:role/firehose-events-delivery"


@pytest.fixture()
def ingestion_infra_settings(settings: SettingsWrapper) -> SettingsWrapper:
    settings.INGESTION_EVENTS_BUCKET_PREFIX = "flagsmith-events-lake-test"
    settings.INGESTION_FIREHOSE_DELIVERY_ROLE_ARN = DELIVERY_ROLE_ARN
    return settings


@pytest.fixture()
def aws_backends(aws_credentials: None) -> Iterator[None]:
    ingestion_infra_service._get_s3_client.cache_clear()
    ingestion_infra_service._get_firehose_client.cache_clear()
    with mock_s3(), mock_firehose():
        yield
    ingestion_infra_service._get_s3_client.cache_clear()
    ingestion_infra_service._get_firehose_client.cache_clear()


def test_provision_ingestion_infrastructure__no_bucket_prefix__raises_improperly_configured(
    ingestion_infra_settings: SettingsWrapper,
) -> None:
    # Given
    ingestion_infra_settings.INGESTION_EVENTS_BUCKET_PREFIX = ""

    # When / Then
    with pytest.raises(ImproperlyConfigured):
        ingestion_infra_service.provision_ingestion_infrastructure(organisation_id=42)


def test_provision_ingestion_infrastructure__no_delivery_role_arn__raises_improperly_configured(
    ingestion_infra_settings: SettingsWrapper,
) -> None:
    # Given
    ingestion_infra_settings.INGESTION_FIREHOSE_DELIVERY_ROLE_ARN = ""

    # When / Then
    with pytest.raises(ImproperlyConfigured):
        ingestion_infra_service.provision_ingestion_infrastructure(organisation_id=42)


def test_provision_ingestion_infrastructure__fresh_account__creates_bucket_and_stream(
    ingestion_infra_settings: SettingsWrapper,
    aws_backends: None,
    log: StructuredLogCapture,
) -> None:
    # When
    result = ingestion_infra_service.provision_ingestion_infrastructure(
        organisation_id=42,
    )

    # Then
    assert result == IngestionInfrastructure(
        bucket_name="flagsmith-events-lake-test-org-42",
        stream_name="events-ingestion-org-42",
    )

    s3 = boto3.client("s3", region_name="eu-west-2")
    public_access_block = s3.get_public_access_block(Bucket=result.bucket_name)
    assert public_access_block["PublicAccessBlockConfiguration"] == {
        "BlockPublicAcls": True,
        "IgnorePublicAcls": True,
        "BlockPublicPolicy": True,
        "RestrictPublicBuckets": True,
    }
    lifecycle = s3.get_bucket_lifecycle_configuration(Bucket=result.bucket_name)
    assert lifecycle["Rules"] == [
        {
            "ID": "expire-delivery-errors",
            "Filter": {"Prefix": "errors/"},
            "Status": "Enabled",
            "Expiration": {"Days": 30},
        }
    ]

    firehose = boto3.client("firehose", region_name="eu-west-2")
    stream = firehose.describe_delivery_stream(DeliveryStreamName=result.stream_name)[
        "DeliveryStreamDescription"
    ]
    assert stream["DeliveryStreamType"] == "DirectPut"
    destination = stream["Destinations"][0]["ExtendedS3DestinationDescription"]
    assert destination["RoleARN"] == DELIVERY_ROLE_ARN
    assert destination["BucketARN"] == "arn:aws:s3:::flagsmith-events-lake-test-org-42"
    assert destination["Prefix"] == (
        "events/env_key=!{partitionKeyFromQuery:env_key}/"
        "year=!{timestamp:yyyy}/month=!{timestamp:MM}/"
        "day=!{timestamp:dd}/hour=!{timestamp:HH}/"
    )
    assert destination["ErrorOutputPrefix"] == (
        "errors/!{firehose:error-output-type}/"
        "year=!{timestamp:yyyy}/month=!{timestamp:MM}/"
        "day=!{timestamp:dd}/hour=!{timestamp:HH}/"
    )
    assert destination["CompressionFormat"] == "GZIP"
    assert destination["BufferingHints"] == {
        "SizeInMBs": 64,
        "IntervalInSeconds": 300,
    }
    assert destination["DynamicPartitioningConfiguration"] == {
        "Enabled": True,
        "RetryOptions": {"DurationInSeconds": 300},
    }
    assert destination["ProcessingConfiguration"] == {
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
    }

    assert log.events == [
        {
            "level": "info",
            "event": "ingestion_infra.bucket_created",
            "organisation__id": 42,
            "bucket__name": "flagsmith-events-lake-test-org-42",
        },
        {
            "level": "info",
            "event": "ingestion_infra.stream_created",
            "organisation__id": 42,
            "stream__name": "events-ingestion-org-42",
            "bucket__name": "flagsmith-events-lake-test-org-42",
        },
    ]


def test_provision_ingestion_infrastructure__already_provisioned__is_idempotent(
    ingestion_infra_settings: SettingsWrapper,
    aws_backends: None,
    log: StructuredLogCapture,
) -> None:
    # Given
    first = ingestion_infra_service.provision_ingestion_infrastructure(
        organisation_id=42,
    )
    events_after_first_run = list(log.events)

    # When
    second = ingestion_infra_service.provision_ingestion_infrastructure(
        organisation_id=42,
    )

    # Then
    assert second == first
    assert log.events == events_after_first_run


def test_provision_ingestion_infrastructure__bucket_creation_fails__propagates_client_error(
    ingestion_infra_settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_s3 = mocker.Mock()
    mock_s3.create_bucket.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "nope"}},
        "CreateBucket",
    )
    mocker.patch(
        "experimentation.ingestion_infra_service._get_s3_client",
        return_value=mock_s3,
    )

    # When / Then
    with pytest.raises(ClientError, match="AccessDenied"):
        ingestion_infra_service.provision_ingestion_infrastructure(organisation_id=42)


def test_provision_ingestion_infrastructure__stream_creation_fails__propagates_client_error(
    ingestion_infra_settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "experimentation.ingestion_infra_service._get_s3_client",
        return_value=mocker.Mock(),
    )
    mock_firehose_client: Any = mocker.Mock()
    mock_firehose_client.create_delivery_stream.side_effect = ClientError(
        {"Error": {"Code": "LimitExceededException", "Message": "too many"}},
        "CreateDeliveryStream",
    )
    mocker.patch(
        "experimentation.ingestion_infra_service._get_firehose_client",
        return_value=mock_firehose_client,
    )

    # When / Then
    with pytest.raises(ClientError, match="LimitExceededException"):
        ingestion_infra_service.provision_ingestion_infrastructure(organisation_id=42)
