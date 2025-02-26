import json

from edge_api.identities.events import send_migration_event


def test_send_migration_event_calls_put_events_with_correct_arguments(mocker, settings):  # type: ignore[no-untyped-def]  # noqa: E501
    # Given
    project_id = 1
    mocked_client = mocker.patch("edge_api.identities.events.events_client")
    event_bus_name = "identity_migration"
    settings.IDENTITY_MIGRATION_EVENT_BUS_NAME = event_bus_name

    # When
    send_migration_event(project_id)

    # Then
    args, kwargs = mocked_client.put_events.call_args
    assert args == ()
    assert kwargs["Entries"][0]["EventBusName"] == event_bus_name
    assert kwargs["Entries"][0]["Detail"] == json.dumps({"project_id": project_id})
