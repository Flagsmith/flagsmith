import pytest

from environments.identities.models import Identity
from environments.sdk.serializers import IdentifyWithTraitsSerializer


@pytest.mark.parametrize(
    "create_identity_before, persist_traits",
    ((True, True), (True, False), (False, True), (False, False)),
)
def test_identify_with_traits_serializer_runs_identity_integrations_on_create(
    mocker, environment, feature, create_identity_before, persist_traits
):
    # Given
    identifier = "johnnybravo"
    trait_key = "foo"
    trait_value = "bar"

    if create_identity_before:
        Identity.objects.create(identifier=identifier, environment=environment)

    environment.project.organisation.persist_trait_data = persist_traits
    environment.project.organisation.save()

    data = {
        "identifier": identifier,
        "traits": [{"trait_key": trait_key, "trait_value": trait_value}],
    }
    serializer = IdentifyWithTraitsSerializer(
        data=data, context={"environment": environment}
    )

    mock_identify_integrations = mocker.patch(
        "environments.sdk.serializers.identify_integrations", autospec=True
    )

    # When
    assert serializer.is_valid()
    serializer.save()

    # Then
    mock_identify_integrations.assert_called_once()
    call_args = mock_identify_integrations.call_args[0]

    identity = call_args[0]
    assert identity.identifier == identifier
