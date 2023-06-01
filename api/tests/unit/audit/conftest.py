import typing

import pytest as pytest
from django.db.models import Model

from organisations.models import OrganisationRole
from permissions.models import PermissionModel
from projects.models import Project, UserProjectPermission
from projects.permissions import VIEW_AUDIT_LOG


@pytest.fixture()
def view_audit_log_permission(db):
    return PermissionModel.objects.get(key=VIEW_AUDIT_LOG)


@pytest.fixture()
def view_audit_log_user(
    project: Project,
    django_user_model: typing.Type[Model],
    view_audit_log_permission: PermissionModel,
):
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(project.organisation, OrganisationRole.USER)
    user_proj_permission = UserProjectPermission.objects.create(
        user=user, project=project
    )
    user_proj_permission.permissions.add(view_audit_log_permission)
    return user


@pytest.fixture()
def project_admin_user(
    project: Project,
    django_user_model: typing.Type[Model],
):
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(project.organisation, OrganisationRole.USER)
    UserProjectPermission.objects.create(user=user, project=project, admin=True)
    return user


@pytest.fixture()
def project_user(
    project: Project,
    django_user_model: typing.Type[Model],
):
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(project.organisation, OrganisationRole.USER)
    UserProjectPermission.objects.create(user=user, project=project)
    return user
