import io
import logging
import typing

if typing.TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client
    from mypy_boto3_s3.type_defs import CompletedPartTypeDef

logger = logging.getLogger(__name__)


class S3MultipartUploadWriter:
    """
    A file-like writer that streams data to S3 using multipart upload.

    Buffers data until the minimum part size (5MB) is reached, then uploads
    each part. This allows streaming large exports without holding the entire
    payload in memory.
    """

    # S3 multipart upload minimum part size is 5MB (except for the last part)
    MIN_PART_SIZE = 5 * 1024 * 1024

    def __init__(
        self,
        s3_client: "S3Client",
        bucket_name: str,
        key: str,
    ) -> None:
        self._s3_client = s3_client
        self._bucket_name = bucket_name
        self._key = key
        self._buffer = io.BytesIO()
        self._parts: list[CompletedPartTypeDef] = []
        self._part_number = 1
        self._upload_id: str | None = None

    def __enter__(self) -> "S3MultipartUploadWriter":
        response = self._s3_client.create_multipart_upload(
            Bucket=self._bucket_name,
            Key=self._key,
        )
        self._upload_id = response["UploadId"]
        logger.debug("Started multipart upload with ID: %s", self._upload_id)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: typing.Any,
    ) -> None:
        if exc_type is not None:
            # Abort the upload on error
            if self._upload_id:
                self._s3_client.abort_multipart_upload(
                    Bucket=self._bucket_name,
                    Key=self._key,
                    UploadId=self._upload_id,
                )
                logger.warning("Aborted multipart upload due to error: %s", exc_val)
            return

        # Upload any remaining data in the buffer (or an empty part if no data)
        # S3 requires at least one part to complete a multipart upload
        if self._buffer.tell() > 0 or not self._parts:
            self._upload_part()

        assert self._upload_id
        # Complete the multipart upload
        self._s3_client.complete_multipart_upload(
            Bucket=self._bucket_name,
            Key=self._key,
            UploadId=self._upload_id,
            MultipartUpload={"Parts": self._parts},
        )
        logger.debug("Completed multipart upload with %d parts", len(self._parts))

    def write(self, data: bytes) -> None:
        self._buffer.write(data)
        if self._buffer.tell() >= self.MIN_PART_SIZE:
            self._upload_part()

    def _upload_part(self) -> None:
        assert self._upload_id
        self._buffer.seek(0)
        response = self._s3_client.upload_part(
            Bucket=self._bucket_name,
            Key=self._key,
            PartNumber=self._part_number,
            UploadId=self._upload_id,
            Body=self._buffer.read(),
        )
        self._parts.append(
            {
                "PartNumber": self._part_number,
                "ETag": response["ETag"],
            }
        )
        logger.debug("Uploaded part %d", self._part_number)
        self._part_number += 1
        self._buffer = io.BytesIO()
