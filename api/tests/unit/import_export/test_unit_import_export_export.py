import json

from django.core.serializers.json import DjangoJSONEncoder

from import_export.export import export_organisation


def test_export_organisation(
    organisation,
    project,
    environment,
    segment,
    tag,
    feature_segment,
    multivariate_feature,
):
    data = export_organisation(organisation_id=organisation.id)
    assert "pk" not in json.dumps(data, cls=DjangoJSONEncoder)
