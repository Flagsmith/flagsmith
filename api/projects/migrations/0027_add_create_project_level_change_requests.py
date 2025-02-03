from common.projects.permissions import CREATE_PROJECT_LEVEL_CHANGE_REQUESTS
from django.db import migrations

from permissions.models import PROJECT_PERMISSION_TYPE


def remove_default_project_permissions(apps, schema_model):  # pragma: no cover
    PermissionModel = apps.get_model("permissions", "PermissionModel")
    PermissionModel.objects.get(key=CREATE_PROJECT_LEVEL_CHANGE_REQUESTS).delete()


def insert_default_project_permissions(apps, schema_model):
    PermissionModel = apps.get_model("permissions", "PermissionModel")

    create_description = "Ability to create project level change requests."

    PermissionModel.objects.get_or_create(
        key=CREATE_PROJECT_LEVEL_CHANGE_REQUESTS,
        type=PROJECT_PERMISSION_TYPE,
        defaults={"description": create_description},
    )


class Migration(migrations.Migration):

    dependencies = [("projects", "0026_add_change_request_approval_limit_to_projects")]

    operations = [
        migrations.RunPython(
            insert_default_project_permissions,
            reverse_code=remove_default_project_permissions,
        ),
    ]
