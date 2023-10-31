import os
import typing
import uuid
from contextlib import suppress

from django.db import migrations

from permissions.models import PermissionModel


class PostgresOnlyRunSQL(migrations.RunSQL):
    @classmethod
    def from_sql_file(
        cls,
        file_path: typing.Union[str, os.PathLike],
        reverse_sql: typing.Union[str, os.PathLike] = None,
    ) -> "PostgresOnlyRunSQL":
        with open(file_path) as forward_sql:
            with suppress(FileNotFoundError, TypeError):
                with open(reverse_sql) as reverse_sql_file:
                    reverse_sql = reverse_sql_file.read()
            return cls(forward_sql.read(), reverse_sql=reverse_sql)

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor != "postgresql":
            return
        super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor != "postgresql":
            return
        super().database_backwards(app_label, schema_editor, from_state, to_state)


class AddDefaultUUIDs:
    def __init__(self, app_name: str, model_name: str):
        self.app_name = app_name
        self.model_name = model_name

    def __call__(self, apps, schema_editor):
        model_class = apps.get_model(self.app_name, self.model_name)
        to_update = []
        for model in model_class.objects.all():
            model.uuid = uuid.uuid4()
            to_update.append(model)
        model_class.objects.bulk_update(to_update, fields=["uuid"])


def create_new_environment_permissions(
    from_permission_key: str,
    model_class: type,
    reverse_attribute_name: str,
    new_permission_objects: typing.List[PermissionModel],
):
    """
    Whenever we introduce a new permission, more often than not, we do that in
    order to allow users to create more granular permissions.

    But we also need to make sure that the existing users who currently
    have less granular(super set) permissions, also get the new permissions. This function does
    excatly that.

    Args:
        from_permission_key: The permission key of the less granular permission, e.g: MANAGE_IDENTITIES.
        model_class: The model class for which we are creating the new permissions, e.g: UserEnvironmentPermission.
        reverse_attribute_name: The name of the reverse attribute on the model class, e.g: userenvironmentpermission.
        new_permission_objects: The list of the new permission model objects.

    """
    new_environment_permission_through_models = []
    environment_permission_through_model_class = model_class.permissions.through

    for environment_permission in model_class.objects.filter(
        permissions__key=from_permission_key
    ):
        new_environment_permission_through_models.extend(
            [
                environment_permission_through_model_class(
                    **{
                        f"{reverse_attribute_name}_id": environment_permission.id,
                        "permissionmodel_id": permission_model.key,
                    }
                )
                for permission_model in new_permission_objects
            ]
        )

    environment_permission_through_model_class.objects.bulk_create(
        new_environment_permission_through_models
    )
