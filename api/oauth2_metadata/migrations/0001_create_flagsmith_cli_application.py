from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from oauth2_metadata.constants import (
    FLAGSMITH_CLI_CLIENT_ID,
    FLAGSMITH_CLI_CLIENT_NAME,
    FLAGSMITH_CLI_REDIRECT_URIS,
)


def create_flagsmith_cli_application(
    apps: Apps,
    schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    Application = apps.get_model("oauth2_provider", "Application")
    Application.objects.get_or_create(
        client_id=FLAGSMITH_CLI_CLIENT_ID,
        defaults={
            "name": FLAGSMITH_CLI_CLIENT_NAME,
            "client_type": "public",
            "authorization_grant_type": "authorization-code",
            "client_secret": "",
            "redirect_uris": FLAGSMITH_CLI_REDIRECT_URIS,
            "skip_authorization": True,
        },
    )


def delete_flagsmith_cli_application(
    apps: Apps,
    schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    Application = apps.get_model("oauth2_provider", "Application")
    Application.objects.filter(client_id=FLAGSMITH_CLI_CLIENT_ID).delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("oauth2_provider", "0012_add_token_checksum"),
    ]

    operations = [
        migrations.RunPython(
            create_flagsmith_cli_application,
            delete_flagsmith_cli_application,
        ),
    ]
