from collections.abc import Iterator
from typing import Any

import boto3
import pytest
from botocore.exceptions import ClientError
from django.core.exceptions import ImproperlyConfigured
from moto import (  # type: ignore[import-untyped]
    mock_firehose,
    mock_s3,
    mock_sts,
)
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from experimentation import ingestion_infra_service
from experimentation.dataclasses import IngestionInfrastructure

DELIVERY_ROLE_ARN = "arn:aws:iam::123456789012:role/firehose-events-delivery"


@pytest.fixture()
def ingestion_infra_settings(settings: SettingsWrapper) -> SettingsWrapper:
    settings.INGESTION_FIREHOSE_DELIVERY_ROLE_ARN = DELIVERY_ROLE_ARN
    return settings


def _clear_client_caches() -> None:
    ingestion_infra_service._get_s3_client.cache_clear()
    ingestion_infra_service._get_firehose_client.cache_clear()
    ingestion_infra_service._get_account_id.cache_clear()


@pytest.fixture()
def aws_backends(aws_credentials: None) -> Iterator[None]:
    _clear_client_caches()
    with mock_s3(), mock_firehose(), mock_sts():
        yield
    _clear_client_caches()


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
    # Given
    organisation_id = 42

    # When
    result = ingestion_infra_service.provision_ingestion_infrastructure(
        organisation_id=organisation_id,
    )

    # Then
    assert result == IngestionInfrastructure(
        bucket_name="flagsmith-events-lake-org-42-123456789012-eu-west-2-an",
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
            "ID": "expire-objects",
            "Filter": {"Prefix": ""},
            "Status": "Enabled",
            "Expiration": {"Days": 30},
        }
    ]
    tagging = s3.get_bucket_tagging(Bucket=result.bucket_name)
    assert tagging["TagSet"] == [{"Key": "organisation_id", "Value": "42"}]

    firehose = boto3.client("firehose", region_name="eu-west-2")
    stream = firehose.describe_delivery_stream(DeliveryStreamName=result.stream_name)[
        "DeliveryStreamDescription"
    ]
    assert stream["DeliveryStreamType"] == "DirectPut"
    destination = stream["Destinations"][0]["ExtendedS3DestinationDescription"]
    assert destination["RoleARN"] == DELIVERY_ROLE_ARN
    assert (
        destination["BucketARN"]
        == "arn:aws:s3:::flagsmith-events-lake-org-42-123456789012-eu-west-2-an"
    )
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
    stream_tags = firehose.list_tags_for_delivery_stream(
        DeliveryStreamName=result.stream_name
    )
    assert stream_tags["Tags"] == [{"Key": "organisation_id", "Value": "42"}]

    assert log.events == [
        {
            "level": "info",
            "event": "ingestion_infra.bucket_created",
            "organisation__id": 42,
            "bucket__name": "flagsmith-events-lake-org-42-123456789012-eu-west-2-an",
        },
        {
            "level": "info",
            "event": "ingestion_infra.stream_created",
            "organisation__id": 42,
            "stream__name": "events-ingestion-org-42",
            "bucket__name": "flagsmith-events-lake-org-42-123456789012-eu-west-2-an",
        },
    ]


def test_provision_ingestion_infrastructure__bucket_creation__sends_account_regional_namespace_header(
    ingestion_infra_settings: SettingsWrapper,
    aws_backends: None,
) -> None:
    # Given
    captured_headers: list[dict[str, str]] = []
    ingestion_infra_service._get_s3_client().meta.events.register(
        "before-call.s3.CreateBucket",
        lambda params, **kwargs: captured_headers.append(params["headers"]),
    )

    # When
    ingestion_infra_service.provision_ingestion_infrastructure(organisation_id=42)

    # Then
    assert captured_headers[0]["x-amz-bucket-namespace"] == "account-regional"


def test_provision_ingestion_infrastructure__bucket_creation_fails__propagates_client_error(
    ingestion_infra_settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "experimentation.ingestion_infra_service._get_account_id",
        return_value="123456789012",
    )
    mock_s3_client = mocker.Mock()
    mock_s3_client.create_bucket.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "nope"}},
        "CreateBucket",
    )
    mocker.patch(
        "experimentation.ingestion_infra_service._get_s3_client",
        return_value=mock_s3_client,
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
        "experimentation.ingestion_infra_service._get_account_id",
        return_value="123456789012",
    )
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


def test_deprovision_ingestion_infrastructure__existing_resources__deletes_bucket_and_stream(
    ingestion_infra_settings: SettingsWrapper,
    aws_backends: None,
    log: StructuredLogCapture,
) -> None:
    # Given
    result = ingestion_infra_service.provision_ingestion_infrastructure(
        organisation_id=42,
    )

    # When
    ingestion_infra_service.deprovision_ingestion_infrastructure(organisation_id=42)

    # Then
    s3 = boto3.client("s3", region_name="eu-west-2")
    bucket_names = [bucket["Name"] for bucket in s3.list_buckets()["Buckets"]]
    assert result.bucket_name not in bucket_names

    firehose = boto3.client("firehose", region_name="eu-west-2")
    with pytest.raises(ClientError):
        firehose.describe_delivery_stream(DeliveryStreamName=result.stream_name)

    assert {
        "level": "info",
        "event": "ingestion_infra.deprovisioned",
        "organisation__id": 42,
        "bucket__name": result.bucket_name,
        "stream__name": result.stream_name,
    } in log.events


def test_deprovision_ingestion_infrastructure__bucket_with_objects__empties_and_deletes_bucket(
    ingestion_infra_settings: SettingsWrapper,
    aws_backends: None,
) -> None:
    # Given
    result = ingestion_infra_service.provision_ingestion_infrastructure(
        organisation_id=42,
    )
    s3 = boto3.client("s3", region_name="eu-west-2")
    s3.put_object(
        Bucket=result.bucket_name,
        Key="events/env_key=abc/data.json.gz",
        Body=b"{}",
    )

    # When
    ingestion_infra_service.deprovision_ingestion_infrastructure(organisation_id=42)

    # Then
    bucket_names = [bucket["Name"] for bucket in s3.list_buckets()["Buckets"]]
    assert result.bucket_name not in bucket_names
