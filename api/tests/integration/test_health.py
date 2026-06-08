from django.core.cache.backends.db import DatabaseCache
from django.db import DatabaseError
from django.test import Client as DjangoClient
from django.urls import reverse
from pytest_mock import MockerFixture
from rest_framework import status


def test_readiness__database_cache_table_missing__returns_non_200(
    django_client: DjangoClient,
    db: None,
    mocker: MockerFixture,
) -> None:
    # Given
    # Reading from any database-backed cache fails, as it would when the
    # `createcachetable` command never created the table on deployment.
    # If the cache health check were not registered with django-health-check,
    # this would have no effect on readiness — so a non-200 also proves the
    # check is wired into the endpoint.
    mocker.patch.object(
        DatabaseCache,
        "get",
        side_effect=DatabaseError('relation "chargebee-objects" does not exist'),
    )
    url = reverse("health:health_check_home")

    # When
    response = django_client.get(url)

    # Then
    assert response.status_code != status.HTTP_200_OK


def test_readiness__database_cache_tables_present__returns_200(
    django_client: DjangoClient,
    db: None,
    mocker: MockerFixture,
) -> None:
    # Given
    # Every database-backed cache is readable.
    mocker.patch.object(DatabaseCache, "get", return_value=None)
    url = reverse("health:health_check_home")

    # When
    response = django_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
