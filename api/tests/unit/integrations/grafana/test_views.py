import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from integrations.grafana.models import GrafanaOrganisationConfiguration
from organisations.models import Organisation


@pytest.fixture
def grafana_organisation_configuration(
    organisation: Organisation,
) -> GrafanaOrganisationConfiguration:
    return GrafanaOrganisationConfiguration.objects.create(
        organisation=organisation,
        base_url="http://test.com",
        api_key="abc-123",
    )


def test_grafana_organisation_view__create_configuration__persist_expected(
    admin_client_new: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    data = {
        "base_url": "http://test.com",
        "api_key": "abc-123",
    }
    url = reverse(
        "api-v1:organisations:integrations-grafana-list", args=[organisation.id]
    )

    # When
    response = admin_client_new.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        GrafanaOrganisationConfiguration.objects.filter(
            organisation=organisation
        ).count()
        == 1
    )

    created_config = GrafanaOrganisationConfiguration.objects.filter(
        organisation=organisation
    ).first()
    assert created_config.base_url == data["base_url"]
    assert created_config.api_key == data["api_key"]


def test_grafana_organisation_view__create_configuration__existing__return_expected(
    admin_client_new: APIClient,
    organisation: Organisation,
    grafana_organisation_configuration: GrafanaOrganisationConfiguration,
) -> None:
    # Given
    data = {
        "base_url": "http://test.com",
        "api_key": "abc-123",
    }
    url = reverse(
        "api-v1:organisations:integrations-grafana-list", args=[organisation.id]
    )

    # When
    response = admin_client_new.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_grafana_organisation_view__update_configuration__persist_expected(
    admin_client_new: APIClient,
    organisation: Organisation,
    grafana_organisation_configuration: GrafanaOrganisationConfiguration,
) -> None:
    # Given
    data = {
        "base_url": "http://updated.test.com",
        "api_key": "updated-abc-123",
    }
    url = reverse(
        "api-v1:organisations:integrations-grafana-detail",
        args=[organisation.id, grafana_organisation_configuration.id],
    )

    # When
    response = admin_client_new.put(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    updated_config = GrafanaOrganisationConfiguration.objects.filter(
        organisation=organisation
    ).first()
    assert updated_config.base_url == data["base_url"]
    assert updated_config.api_key == data["api_key"]


def test_grafana_organisation_view__delete_configuration__return_expected(
    admin_client_new: APIClient,
    organisation: Organisation,
    grafana_organisation_configuration: GrafanaOrganisationConfiguration,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:integrations-grafana-detail",
        args=[organisation.id, grafana_organisation_configuration.id],
    )

    # When
    response = admin_client_new.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not GrafanaOrganisationConfiguration.objects.filter(
        organisation=organisation
    ).exists()


def test_grafana_organisation_view__create_configuration__non_admin__return_expected(
    test_user_client: APIClient,
    organisation: Organisation,
    grafana_organisation_configuration: GrafanaOrganisationConfiguration,
) -> None:
    # Given
    data = {
        "base_url": "http://test.com",
        "api_key": "abc-123",
    }
    url = reverse(
        "api-v1:organisations:integrations-grafana-list", args=[organisation.id]
    )

    # When
    response = test_user_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_grafana_organisation_view__get_configuration__non_admin__return_expected(
    test_user_client: APIClient,
    organisation: Organisation,
    grafana_organisation_configuration: GrafanaOrganisationConfiguration,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:integrations-grafana-detail",
        args=[organisation.id, grafana_organisation_configuration.id],
    )

    # When
    response = test_user_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_grafana_organisation_view__delete_configuration__non_admin__return_expected(
    test_user_client: APIClient,
    organisation: Organisation,
    grafana_organisation_configuration: GrafanaOrganisationConfiguration,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:integrations-grafana-detail",
        args=[organisation.id, grafana_organisation_configuration.id],
    )

    # When
    response = test_user_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
