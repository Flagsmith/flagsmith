import typing
import uuid

from django.db import migrations, models


class PostgresOnlyRunSQL(migrations.RunSQL):
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor != "postgresql":
            return
        super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor != "postgresql":
            return
        super().database_backwards(app_label, schema_editor, from_state, to_state)


def add_default_uuids(model_class: typing.Type[models.Model]) -> None:
    to_update = []
    for model in model_class.objects.all():
        model.uuid = uuid.uuid4()
        to_update.append(model)
    model_class.objects.bulk_update(to_update, fields=["uuid"])
