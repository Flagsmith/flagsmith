import pytest
from django.contrib.contenttypes.models import ContentType

from metadata.models import MetadataField, MetadataModelField
from organisations.models import Organisation


@pytest.fixture
def environment_metadata_field_different_org(environment):
    another_organisation = Organisation.objects.create(name="Another organisation")
    another_field = MetadataField.objects.create(
        name="Another field",
        description="Another field",
        type="int",
        organisation=another_organisation,
    )

    environment_type = ContentType.objects.get_for_model(environment)
    return MetadataModelField.objects.create(
        content_type=environment_type,
        field=another_field,
    )
