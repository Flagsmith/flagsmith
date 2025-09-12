from django.contrib.admin.sites import AdminSite
from pytest_mock import MockerFixture

from environments.admin import EnvironmentAdmin
from environments.models import Environment


def test_environment_admin_rebuild_environments(
    environment: Environment, mocker: MockerFixture
) -> None:
    # GIVEN
    mocked_rebuild_environment_document = mocker.patch(
        "environments.admin.rebuild_environment_document"
    )
    environment_admin = EnvironmentAdmin(Environment, AdminSite())
    # WHEN
    environment_admin.rebuild_environments(
        request=mocker.MagicMock(), queryset=Environment.objects.all()
    )
    # THEN
    mocked_rebuild_environment_document.delay.assert_called_once_with(
        args=(environment.id,)
    )
