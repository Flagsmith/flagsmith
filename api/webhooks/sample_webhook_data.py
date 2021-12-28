environment_webhook_data = {
    "data": {
        "changed_by": "Ben Rometsch",
        "new_state": {
            "enabled": True,
            "environment": {"id": 23, "name": "Development"},
            "feature": {
                "created_date": "2021-02-10T20:03:43.348556Z",
                "default_enabled": False,
                "description": "Show html in a butter bar for certain users",
                "id": 7168,
                "initial_value": None,
                "name": "butter_bar",
                "project": {"id": 12, "name": "Flagsmith Website"},
                "type": "CONFIG",
            },
            "feature_segment": None,
            "feature_state_value": "\nYou are using the develop environment.\n",
            "identity": None,
            "identity_identifier": None,
        },
        "previous_state": {
            "enabled": False,
            "environment": {"id": 23, "name": "Development"},
            "feature": {
                "created_date": "2021-02-10T20:03:43.348556Z",
                "default_enabled": False,
                "description": "Show html in a butter bar for certain users",
                "id": 7168,
                "initial_value": None,
                "name": "butter_bar",
                "project": {"id": 12, "name": "Flagsmith Website"},
                "type": "CONFIG",
            },
            "feature_segment": None,
            "feature_state_value": "\nYou are using the develop environment.\n",
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
            "id": 3,
            "email": "user@domain.com",
            "first_name": "Kyle",
            "last_name": "Johnson",
        },
        "environment": None,
        "project": {"id": 6, "name": "Project name", "organisation": 1},
        "related_object_id": 6,
        "related_object_type": "FEATURE",
    },
    "event_type": "AUDIT_LOG_CREATED",
}
