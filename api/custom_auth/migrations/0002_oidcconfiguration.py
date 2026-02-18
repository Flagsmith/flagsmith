from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("custom_auth", "0001_initial"),
        ("organisations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="OIDCConfiguration",
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
                    "name",
                    models.SlugField(
                        unique=True,
                        help_text="URL-friendly identifier for this OIDC configuration.",
                    ),
                ),
                (
                    "provider_url",
                    models.URLField(
                        help_text="The base URL of the OIDC provider (e.g., https://keycloak.example.com/realms/myrealm)."
                    ),
                ),
                ("client_id", models.CharField(max_length=200)),
                ("client_secret", models.CharField(max_length=200)),
                (
                    "frontend_url",
                    models.URLField(
                        blank=True,
                        default="",
                        help_text="The base URL of the Flagsmith dashboard. Users will be redirected here after authentication.",
                    ),
                ),
                (
                    "allow_idp_initiated",
                    models.BooleanField(
                        default=False,
                        help_text="Allow logins initiated by the identity provider.",
                    ),
                ),
                (
                    "organisation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="oidc_configurations",
                        to="organisations.organisation",
                    ),
                ),
            ],
        ),
    ]
