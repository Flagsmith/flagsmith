import json

import boto3
from django.core.serializers.json import DjangoJSONEncoder
from moto import mock_s3

from import_export.export import export_organisation
from import_export.import_ import OrganisationImporter
from organisations.models import Organisation


@mock_s3
def test_import_organisation(organisation):
    # Given
    bucket_name = "test-bucket"
    file_key = "organisation-exports/org-1.json"

    s3_resource = boto3.resource("s3", region_name="eu-west-2")
    s3_resource.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )

    body = json.dumps(
        export_organisation(organisation.id), cls=DjangoJSONEncoder
    ).encode("utf-8")

    s3_client = boto3.client("s3")
    s3_client.put_object(Body=body, Bucket=bucket_name, Key=file_key)

    importer = OrganisationImporter(s3_client=s3_client)

    # When
    importer.import_organisation(bucket_name, file_key)

    # Then
    assert Organisation.objects.filter(id=organisation.id).count() == 1
