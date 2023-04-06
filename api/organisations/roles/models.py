from django.db import models

from environments.models import Environment
from organisations.models import Organisation
from permissions.models import AbstractBasePermissionModel
from projects.models import Project
from users.models import FFAdminUser, UserPermissionGroup


class Role(models.Model):
    name = models.CharField(max_length=2000)
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="roles",
        related_query_name="role",
    )


class RoleOrganisationPermission(AbstractBasePermissionModel):
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_query_name="org_role_permission",
    )


class RoleProjectPermission(AbstractBasePermissionModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_query_name="rolepermission"
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    admin = models.BooleanField(default=False)


class RoleEnvironmentPermission(AbstractBasePermissionModel):
    environment = models.ForeignKey(
        Environment, on_delete=models.CASCADE, related_query_name="rolepermission"
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    admin = models.BooleanField(default=False)


class UserRole(models.Model):
    user = models.ForeignKey(FFAdminUser, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="userrole")


class GroupRole(models.Model):
    group = models.ForeignKey(UserPermissionGroup, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="grouprole")
