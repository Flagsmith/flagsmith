import os
import uuid

import boto3
from django.core.management import call_command


class OrganisationImporter:
    def __init__(self, s3_client=None):
        self._s3_client = s3_client or boto3.client("s3")

    def import_organisation(self, s3_bucket: str, s3_key: str) -> None:
        obj = self._s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        file_path = f"/tmp/{uuid.uuid4()}.json"

        with open(file_path, "w+") as f:
            f.write(obj["Body"].read().decode("utf-8"))

        with open(file_path, "r") as f:
            try:
                call_command("loaddata", f.name, format="json")
            finally:
                os.remove(f.name)
