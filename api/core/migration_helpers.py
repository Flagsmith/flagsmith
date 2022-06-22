import uuid

from django.db import migrations


class PostgresOnlyRunSQL(migrations.RunSQL):
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
