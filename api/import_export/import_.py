import logging
import uuid

import boto3
from django.core.management import call_command

logger = logging.getLogger(__name__)


class OrganisationImporter:
    def __init__(self, s3_client=None):  # type: ignore[no-untyped-def]
        self._s3_client = s3_client or boto3.client("s3")

    def import_organisation(self, s3_bucket: str, s3_key: str) -> None:
        """
        Import an organisation from a json file containing the django fixtures
        as exported by the `export` module in this package.

        This code essentially acts as a wrapper to the django loaddata management
        command to grab a file from S3 and read from that.

        Since loaddata only accepts the name of a fixture or the path to a fixture
        file, we have to store the data in a local file before passing it to the
        call_command function. We store it in /tmp/ with a unique uuid and remove it
        after, regardless of the success of the task to ensure we're not clogging up
        the task's storage.
        """

        logger.info("Starting organisation import.")

        obj = self._s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        file_path = f"/tmp/{uuid.uuid4()}.json"

        with open(file_path, "a+") as f:
            logger.debug("Writing file to '%s'", file_path)
            f.write(obj["Body"].read().decode("utf-8"))
            logger.debug("Finished writing file.")
            f.seek(0)
            logger.debug("Calling loaddata")
            call_command("loaddata", f.name, format="json")
            logger.debug("Finished loading data")
