import os
import uuid

import boto3
from django.core.management import call_command

s3 = None


def get_client():
    global s3

    if not s3:
        s3 = boto3.client("s3")

    return s3


def import_organisation(from_s3_bucket: str, path: str, s3_client=None) -> None:
    s3_client = s3_client or get_client()

    obj = s3_client.get_object(Bucket=from_s3_bucket, Key=path)
    file_path = f"/tmp/{uuid.uuid4()}.json"

    with open(file_path, "w+") as f:
        f.write(obj["Body"].read().decode("utf-8"))

    with open(file_path, "r") as f:
        try:
            call_command("loaddata", f.name, format="json")
        finally:
            os.remove(f.name)
