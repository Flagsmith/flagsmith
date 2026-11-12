from django.contrib.auth.hashers import check_password
from django_test_migrations.migrator import Migrator


def test_0001__fresh_install__creates_flagsmith_cli_application(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(("oauth2_metadata", None))
    OldApplication = old_state.apps.get_model("oauth2_provider", "Application")
    OldApplication.objects.filter(client_id="flagsmith-cli").delete()

    # When
    new_state = migrator.apply_tested_migration(
        ("oauth2_metadata", "0001_create_flagsmith_cli_application")
    )

    # Then
    Application = new_state.apps.get_model("oauth2_provider", "Application")
    application = Application.objects.get(client_id="flagsmith-cli")
    assert application.name == "Flagsmith CLI"
    assert application.client_type == "public"
    assert application.authorization_grant_type == "authorization-code"
    # The client_secret field hashes on save; the stored value must be the
    # hash of an empty secret (public client, token_endpoint_auth "none").
    assert check_password("", application.client_secret)
    assert (
        application.redirect_uris == "http://127.0.0.1/callback http://[::1]/callback"
    )
    assert application.skip_authorization is True


def test_0001__application_already_exists__does_not_overwrite(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(("oauth2_metadata", None))
    OldApplication = old_state.apps.get_model("oauth2_provider", "Application")
    OldApplication.objects.filter(client_id="flagsmith-cli").delete()
    OldApplication.objects.create(
        client_id="flagsmith-cli",
        name="Pre-existing Application",
        client_type="confidential",
        authorization_grant_type="client-credentials",
        client_secret="pre-existing-secret",
        redirect_uris="https://example.com/callback",
        skip_authorization=False,
    )

    # When
    new_state = migrator.apply_tested_migration(
        ("oauth2_metadata", "0001_create_flagsmith_cli_application")
    )

    # Then
    Application = new_state.apps.get_model("oauth2_provider", "Application")
    application = Application.objects.get(client_id="flagsmith-cli")
    assert application.name == "Pre-existing Application"
    assert application.client_type == "confidential"
    assert application.authorization_grant_type == "client-credentials"
    assert check_password("pre-existing-secret", application.client_secret)
    assert application.redirect_uris == "https://example.com/callback"
    assert application.skip_authorization is False
