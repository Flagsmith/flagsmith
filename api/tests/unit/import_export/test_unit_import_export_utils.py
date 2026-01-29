from unittest.mock import MagicMock, call

import pytest

from import_export.utils import S3MultipartUploadWriter


@pytest.fixture
def s3_client() -> MagicMock:
    client = MagicMock()
    client.create_multipart_upload.return_value = {"UploadId": "test-upload-id"}
    client.upload_part.return_value = {"ETag": "test-etag"}
    return client


def test_s3_multipart_upload_writer__single_part__completes_upload(
    s3_client: MagicMock,
) -> None:
    # Given
    bucket_name = "test-bucket"
    key = "test-key"
    data = b"small data"

    # When
    with S3MultipartUploadWriter(s3_client, bucket_name, key) as writer:
        writer.write(data)

    # Then
    s3_client.create_multipart_upload.assert_called_once_with(
        Bucket=bucket_name,
        Key=key,
    )
    s3_client.upload_part.assert_called_once_with(
        Bucket=bucket_name,
        Key=key,
        PartNumber=1,
        UploadId="test-upload-id",
        Body=data,
    )
    s3_client.complete_multipart_upload.assert_called_once_with(
        Bucket=bucket_name,
        Key=key,
        UploadId="test-upload-id",
        MultipartUpload={"Parts": [{"PartNumber": 1, "ETag": "test-etag"}]},
    )
    s3_client.abort_multipart_upload.assert_not_called()


def test_s3_multipart_upload_writer__multiple_parts__uploads_each_part(
    s3_client: MagicMock,
) -> None:
    # Given
    bucket_name = "test-bucket"
    key = "test-key"
    # Create data larger than MIN_PART_SIZE (5MB)
    chunk_size = S3MultipartUploadWriter.MIN_PART_SIZE
    first_chunk = b"a" * chunk_size
    second_chunk = b"b" * chunk_size
    final_chunk = b"final"

    s3_client.upload_part.side_effect = [
        {"ETag": "etag-1"},
        {"ETag": "etag-2"},
        {"ETag": "etag-3"},
    ]

    # When
    with S3MultipartUploadWriter(s3_client, bucket_name, key) as writer:
        writer.write(first_chunk)
        writer.write(second_chunk)
        writer.write(final_chunk)

    # Then
    assert s3_client.upload_part.call_count == 3
    s3_client.upload_part.assert_has_calls(
        [
            call(
                Bucket=bucket_name,
                Key=key,
                PartNumber=1,
                UploadId="test-upload-id",
                Body=first_chunk,
            ),
            call(
                Bucket=bucket_name,
                Key=key,
                PartNumber=2,
                UploadId="test-upload-id",
                Body=second_chunk,
            ),
            call(
                Bucket=bucket_name,
                Key=key,
                PartNumber=3,
                UploadId="test-upload-id",
                Body=final_chunk,
            ),
        ]
    )
    s3_client.complete_multipart_upload.assert_called_once_with(
        Bucket=bucket_name,
        Key=key,
        UploadId="test-upload-id",
        MultipartUpload={
            "Parts": [
                {"PartNumber": 1, "ETag": "etag-1"},
                {"PartNumber": 2, "ETag": "etag-2"},
                {"PartNumber": 3, "ETag": "etag-3"},
            ]
        },
    )


def test_s3_multipart_upload_writer__accumulates_small_writes__uploads_when_threshold_reached(
    s3_client: MagicMock,
) -> None:
    # Given
    bucket_name = "test-bucket"
    key = "test-key"
    small_chunk = b"x" * 1000  # 1KB
    writes_to_reach_threshold = (S3MultipartUploadWriter.MIN_PART_SIZE // 1000) + 1

    s3_client.upload_part.side_effect = [
        {"ETag": "etag-1"},
        {"ETag": "etag-2"},
    ]

    # When
    with S3MultipartUploadWriter(s3_client, bucket_name, key) as writer:
        for _ in range(writes_to_reach_threshold):
            writer.write(small_chunk)
        # Write one more small chunk to have remaining data
        writer.write(b"final")

    # Then
    # Should have uploaded one part when threshold was reached,
    # and one final part with remaining data on exit
    assert s3_client.upload_part.call_count == 2


def test_s3_multipart_upload_writer__error_during_write__aborts_upload(
    s3_client: MagicMock,
) -> None:
    # Given
    bucket_name = "test-bucket"
    key = "test-key"

    # When
    with pytest.raises(ValueError, match="test error"):
        with S3MultipartUploadWriter(s3_client, bucket_name, key) as writer:
            writer.write(b"some data")
            raise ValueError("test error")

    # Then
    s3_client.abort_multipart_upload.assert_called_once_with(
        Bucket=bucket_name,
        Key=key,
        UploadId="test-upload-id",
    )
    s3_client.complete_multipart_upload.assert_not_called()


def test_s3_multipart_upload_writer__no_data__completes_with_no_parts(
    s3_client: MagicMock,
) -> None:
    # Given
    bucket_name = "test-bucket"
    key = "test-key"

    # When
    with S3MultipartUploadWriter(s3_client, bucket_name, key):
        pass  # No writes

    # Then
    s3_client.upload_part.assert_not_called()
    s3_client.complete_multipart_upload.assert_called_once_with(
        Bucket=bucket_name,
        Key=key,
        UploadId="test-upload-id",
        MultipartUpload={"Parts": []},
    )


def test_s3_multipart_upload_writer__multiple_small_writes__buffers_correctly(
    s3_client: MagicMock,
) -> None:
    # Given
    bucket_name = "test-bucket"
    key = "test-key"

    # When
    with S3MultipartUploadWriter(s3_client, bucket_name, key) as writer:
        writer.write(b"hello ")
        writer.write(b"world")

    # Then
    # Both writes should be buffered and uploaded as single part
    s3_client.upload_part.assert_called_once_with(
        Bucket=bucket_name,
        Key=key,
        PartNumber=1,
        UploadId="test-upload-id",
        Body=b"hello world",
    )
