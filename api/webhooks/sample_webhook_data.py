environment_webhook_data = {
    "data": {
        "changed_by": "John Doe",
        "new_state": {
            "enabled": True,
            "environment": {"id": 1, "name": "Development"},
            "feature": {
                "created_date": "2021-02-10T20:03:43.348556Z",
                "default_enabled": False,
                "description": "This is a description",
                "id": 1,
                "initial_value": None,
                "name": "test_feature",
                "project": {"id": 1, "name": "Test Project"},
                "type": "CONFIG",
            },
            "feature_segment": None,
            "feature_state_value": "feature_state_value",
            "identity": None,
            "identity_identifier": None,
        },
        "previous_state": {
            "enabled": False,
            "environment": {"id": 1, "name": "Development"},
            "feature": {
                "created_date": "2021-02-10T20:03:43.348556Z",
                "default_enabled": False,
                "description": "This is description",
                "id": 1,
                "initial_value": None,
                "name": "test_feature",
                "project": {"id": 1, "name": "Test Project"},
                "type": "CONFIG",
            },
            "feature_segment": None,
            "feature_state_value": "old_feature_state_value",
            "identity": None,
            "identity_identifier": None,
        },
        "timestamp": "2021-06-18T07:50:26.595298Z",
    },
    "event_type": "FLAG_UPDATED",
}

organisation_webhook_data = {
    "data": {
        "created_date": "2020-02-23T17:30:57.006318Z",
        "log": "New Flag / Remote Config created: my_feature",
        "author": {
            "id": 1,
            "email": "user@domain.com",
            "first_name": "Jane",
            "last_name": "Doe",
        },
        "environment": None,
        "project": {"id": 1, "name": "Test Project", "organisation": 1},
        "related_object_id": 1,
        "related_object_type": "FEATURE",
    },
    "event_type": "AUDIT_LOG_CREATED",
}
