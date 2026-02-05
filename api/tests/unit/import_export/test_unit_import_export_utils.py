import boto3
from moto import mock_s3  # type: ignore[import-untyped]
from pytest_mock import MockerFixture

from import_export.utils import S3MultipartUploadWriter


@mock_s3  # type: ignore[misc]
def test_s3_multipart_upload_writer__single_part__completes_upload() -> None:
    # Given
    bucket_name = "test-bucket"
    key = "test-key"
    data = b"small data"

    s3_resource = boto3.resource("s3", region_name="eu-west-2")
    s3_resource.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )
    s3_client = boto3.client("s3", region_name="eu-west-2")

    # When
    with S3MultipartUploadWriter(s3_client, bucket_name, key) as writer:
        writer.write(data)

    # Then
    result = s3_client.get_object(Bucket=bucket_name, Key=key)
    assert result["Body"].read() == data


@mock_s3  # type: ignore[misc]
def test_s3_multipart_upload_writer__multiple_parts__uploads_each_part(
    mocker: MockerFixture,
) -> None:
    # Given
    bucket_name = "test-bucket"
    key = "test-key"
    # Create data larger than MIN_PART_SIZE (5MB)
    chunk_size = S3MultipartUploadWriter.MIN_PART_SIZE
    first_chunk = b"a" * chunk_size
    second_chunk = b"b" * chunk_size
    final_chunk = b"final"

    s3_resource = boto3.resource("s3", region_name="eu-west-2")
    s3_resource.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )
    s3_client = boto3.client("s3", region_name="eu-west-2")
    upload_part_spy = mocker.spy(s3_client, "upload_part")

    # When
    with S3MultipartUploadWriter(s3_client, bucket_name, key) as writer:
        writer.write(first_chunk)
        writer.write(second_chunk)
        writer.write(final_chunk)

    # Then
    result = s3_client.get_object(Bucket=bucket_name, Key=key)
    assert result["Body"].read() == first_chunk + second_chunk + final_chunk

    # Verify exactly 3 parts were uploaded
    assert upload_part_spy.call_count == 3
    # Verify part numbers are sequential
    part_numbers = [
        call.kwargs["PartNumber"] for call in upload_part_spy.call_args_list
    ]
    assert part_numbers == [1, 2, 3]


@mock_s3  # type: ignore[misc]
def test_s3_multipart_upload_writer__accumulates_small_writes__uploads_correctly(
    mocker: MockerFixture,
) -> None:
    # Given
    bucket_name = "test-bucket"
    key = "test-key"
    small_chunk = b"x" * 1000  # 1KB
    writes_to_reach_threshold = (S3MultipartUploadWriter.MIN_PART_SIZE // 1000) + 1

    s3_resource = boto3.resource("s3", region_name="eu-west-2")
    s3_resource.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )
    s3_client = boto3.client("s3", region_name="eu-west-2")
    upload_part_spy = mocker.spy(s3_client, "upload_part")

    # When
    with S3MultipartUploadWriter(s3_client, bucket_name, key) as writer:
        for _ in range(writes_to_reach_threshold):
            writer.write(small_chunk)
        writer.write(b"final")

    # Then
    result = s3_client.get_object(Bucket=bucket_name, Key=key)
    expected_data = (small_chunk * writes_to_reach_threshold) + b"final"
    assert result["Body"].read() == expected_data

    # Verify buffering: one part when threshold reached, one final part on exit
    assert upload_part_spy.call_count == 2


@mock_s3  # type: ignore[misc]
def test_s3_multipart_upload_writer__error_during_write__aborts_upload() -> None:
    # Given
    bucket_name = "test-bucket"
    key = "test-key"

    s3_resource = boto3.resource("s3", region_name="eu-west-2")
    s3_resource.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )
    s3_client = boto3.client("s3", region_name="eu-west-2")

    # When
    try:
        with S3MultipartUploadWriter(s3_client, bucket_name, key) as writer:
            writer.write(b"some data")
            raise ValueError("test error")
    except ValueError:
        pass

    # Then - the object should not exist (upload was aborted)
    objects = s3_client.list_objects_v2(Bucket=bucket_name)
    assert objects.get("KeyCount", 0) == 0


@mock_s3  # type: ignore[misc]
def test_s3_multipart_upload_writer__no_data__completes_with_empty_object() -> None:
    # Given
    bucket_name = "test-bucket"
    key = "test-key"

    s3_resource = boto3.resource("s3", region_name="eu-west-2")
    s3_resource.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )
    s3_client = boto3.client("s3", region_name="eu-west-2")

    # When
    with S3MultipartUploadWriter(s3_client, bucket_name, key):
        pass  # No writes

    # Then
    result = s3_client.get_object(Bucket=bucket_name, Key=key)
    assert result["Body"].read() == b""


@mock_s3  # type: ignore[misc]
def test_s3_multipart_upload_writer__multiple_small_writes__buffers_correctly(
    mocker: MockerFixture,
) -> None:
    # Given
    bucket_name = "test-bucket"
    key = "test-key"

    s3_resource = boto3.resource("s3", region_name="eu-west-2")
    s3_resource.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )
    s3_client = boto3.client("s3", region_name="eu-west-2")
    upload_part_spy = mocker.spy(s3_client, "upload_part")

    # When
    with S3MultipartUploadWriter(s3_client, bucket_name, key) as writer:
        writer.write(b"hello ")
        writer.write(b"world")

    # Then
    result = s3_client.get_object(Bucket=bucket_name, Key=key)
    assert result["Body"].read() == b"hello world"

    # Verify both writes were buffered and uploaded as a single part
    assert upload_part_spy.call_count == 1
