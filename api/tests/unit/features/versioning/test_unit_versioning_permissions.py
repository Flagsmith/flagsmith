import pytest
from django.http import Http404
from pytest_mock import MockerFixture
from rest_framework.request import Request
from rest_framework.viewsets import GenericViewSet

from environments.models import Environment
from features.models import Feature
from features.versioning.permissions import (
    EnvironmentFeatureVersionFeatureStatePermissions,
    EnvironmentFeatureVersionPermissions,
)
from users.models import FFAdminUser

pytestmark = pytest.mark.django_db


def test_environment_feature_version_feature_state_permissions__missing_environment__raises_404(
    admin_user: FFAdminUser,
    mocker: MockerFixture,
) -> None:
    # Given
    request = mocker.MagicMock(spec=Request, user=admin_user)
    view = mocker.MagicMock(
        spec=GenericViewSet,
        action="list",
        kwargs={"environment_pk": 1000000},
    )

    # When / Then
    with pytest.raises(Http404):
        EnvironmentFeatureVersionFeatureStatePermissions().has_permission(request, view)


def test_environment_feature_version_permissions__missing_feature__raises_404(
    admin_user: FFAdminUser,
    environment: Environment,
    feature: Feature,
    mocker: MockerFixture,
) -> None:
    # Given
    request = mocker.MagicMock(spec=Request, user=admin_user)
    view = mocker.MagicMock(
        spec=GenericViewSet,
        action="create",
        kwargs={
            "environment_pk": environment.id,
            "feature_pk": feature.id + 1000000,
        },
    )

    # When / Then
    with pytest.raises(Http404):
        EnvironmentFeatureVersionPermissions().has_permission(request, view)
