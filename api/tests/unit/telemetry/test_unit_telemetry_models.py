from django.test import override_settings
from telemetry.models import TelemetryData

env = "test"
debug_enabled = True


@override_settings(ENV=env, DEBUG=debug_enabled)
def test_get_install_stats(
    organisation_one,
    organisation_two,
    organisation_one_project_one,
    organisation_one_project_two,
    organisation_two_project_one,
    organisation_two_project_two,
    organisation_one_project_one_environment_one,
    organisation_one_project_one_environment_two,
    organisation_two_project_one_environment_one,
    organisation_two_project_one_environment_two,
    user_one,
):
    # When
    telemetry_data = TelemetryData.generate_telemetry_data()

    # Then
    assert telemetry_data.organisations == 2
    assert telemetry_data.projects == 4
    assert telemetry_data.features == 0
    assert telemetry_data.segments == 0
    assert telemetry_data.environments == 4
    assert telemetry_data.users == 1
    assert telemetry_data.env == env
    assert telemetry_data.debug_enabled == debug_enabled
