from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor



def create_flagsmith_cli_application(
    apps: Apps,
    schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    Application = apps.get_model("oauth2_provider", "Application")
    Application.objects.get_or_create(
        client_id="flagsmith-cli",
        defaults={
            "name": "Flagsmith CLI",
            "client_type": "public",
            "authorization_grant_type": "authorization-code",
            "client_secret": "",
            "redirect_uris": "http://127.0.0.1/callback http://[::1]/callback",
            "skip_authorization": True,
        },
    )


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("oauth2_provider", "0012_add_token_checksum"),
    ]

    operations = [
        migrations.RunPython(
            create_flagsmith_cli_application,
            migrations.RunPython.noop,
        ),
    ]
