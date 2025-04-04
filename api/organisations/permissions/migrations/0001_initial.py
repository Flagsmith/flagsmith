# Generated by Django 2.2.24 on 2021-12-13 14:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from organisations.models import OrganisationRole
from organisations.permissions.permissions import CREATE_PROJECT


def add_create_project_permission_to_existing_users(apps, schema_editor):  # type: ignore[no-untyped-def]
    user_organisation_permission_model_class = apps.get_model(
        "organisation_permissions", "UserOrganisationPermission"
    )
    user_organisation_model_class = apps.get_model("organisations", "UserOrganisation")
    through_model_class = user_organisation_permission_model_class.permissions.through

    # generate the user organisation permission models without any permissions
    user_permission_models = []
    for user_organisation in user_organisation_model_class.objects.filter(
        role=OrganisationRole.USER.name
    ):
        user_permission_models.append(
            user_organisation_permission_model_class(
                user=user_organisation.user, organisation=user_organisation.organisation
            )
        )
    user_organisation_permission_model_class.objects.bulk_create(user_permission_models)

    # use the through model so that we can bulk create the actual permissions
    through_models = []
    for user_organisation_permission in user_permission_models:
        through_models.append(
            through_model_class(
                userorganisationpermission_id=user_organisation_permission.id,
                permissionmodel_id=CREATE_PROJECT,
            )
        )
    through_model_class.objects.bulk_create(through_models)


def reverse(apps, schema_editor):  # type: ignore[no-untyped-def]
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0029_auto_20210223_1603"),
        ("permissions", "0004_add_create_project_permission"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organisations", "0027_organisation_restrict_project_create_to_admin"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrganisationPermissionModel",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("permissions.permissionmodel",),
        ),
        migrations.CreateModel(
            name="UserPermissionGroupOrganisationPermission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.UserPermissionGroup",
                    ),
                ),
                (
                    "organisation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="organisations.Organisation",
                    ),
                ),
                (
                    "permissions",
                    models.ManyToManyField(
                        blank=True, to="permissions.PermissionModel"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="UserOrganisationPermission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "organisation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="organisations.Organisation",
                    ),
                ),
                (
                    "permissions",
                    models.ManyToManyField(
                        blank=True, to="permissions.PermissionModel"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.RunPython(
            add_create_project_permission_to_existing_users, reverse_code=reverse
        ),
    ]
