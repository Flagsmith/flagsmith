import pytest
from core.request_origin import RequestOrigin
from django.db.models import Q
from pytest_mock import MockerFixture

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from environments.sdk.serializers import IdentifyWithTraitsSerializer
from features.models import Feature


@pytest.mark.parametrize(
    "create_identity_before, persist_traits",
    ((True, True), (True, False), (False, True), (False, False)),
)
def test_identify_with_traits_serializer_runs_identity_integrations_on_create(
    mocker: MockerFixture,
    environment: Environment,
    create_identity_before: bool,
    persist_traits: bool,
) -> None:
    # Given
    identifier = "johnnybravo"
    trait_key = "foo"
    trait_value = "bar"

    if create_identity_before:
        Identity.objects.create(identifier=identifier, environment=environment)

    environment.project.organisation.persist_trait_data = persist_traits
    environment.project.organisation.save()

    mock_request = mocker.MagicMock(originated_from=RequestOrigin.CLIENT)

    data = {
        "identifier": identifier,
        "traits": [{"trait_key": trait_key, "trait_value": trait_value}],
    }
    serializer = IdentifyWithTraitsSerializer(
        data=data, context={"environment": environment, "request": mock_request}
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


def test_identify_with_traits_serializer__additional_filters_in_context__filters_expected(
    mocker: MockerFixture,
    environment: Environment,
    feature: Feature,
    identity: Identity,
) -> None:
    # Given
    data = {
        "identifier": identity.identifier,
        "traits": [],
    }
    request_mock = mocker.MagicMock()

    serializer = IdentifyWithTraitsSerializer(
        data=data,
        context={
            "environment": environment,
            "request": request_mock,
            "feature_states_additional_filters": ~Q(feature_id=feature.id),
        },
    )

    # When
    assert serializer.is_valid()
    serializer.save()

    # Then
    assert "flags" not in serializer.data


def test_identify_with_traits_serializer__transient__identity_and_traits_not_persisted(
    mocker: MockerFixture,
    environment: Environment,
) -> None:
    # Given
    identity_identifier = "completely_new_identity"
    data = {
        "identifier": identity_identifier,
        "traits": [{"trait_key": "trait_key", "trait_value": "trait_value"}],
        "transient": True,
    }
    request_mock = mocker.MagicMock()

    serializer = IdentifyWithTraitsSerializer(
        data=data,
        context={
            "environment": environment,
            "request": request_mock,
        },
    )

    # When
    assert serializer.is_valid()
    serializer.save()

    # Then
    assert not Identity.objects.filter(identifier=identity_identifier).exists()
    assert not Trait.objects.filter(identity__identifier=identity_identifier).exists()
