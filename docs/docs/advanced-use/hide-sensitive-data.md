# Hide Sensitive Data

If turned on (for the environment) this will remove the following fields from the SDK endpoints response:

- `id`
- `created_date`
- `description`
- `initial_value`
- `default_enabled`
- `feature_segment`
- `environment`
- `traits`

e.g: the response from `/api/v1/flags` will change from this:

```
[
    {
        "id": 27595,
        "feature": {
            "id": 9422,
            "name": "first_feature",
            "created_date": "2023-05-14T06:11:08.178802Z",
            "description": null,
            "initial_value": null,
            "default_enabled": false,
            "type": "STANDARD"
        },
        "feature_state_value": null,
        "environment": 5242,
        "identity": null,
        "feature_segment": null,
        "enabled": false
    },
    {
        "id": 27597,
        "feature": {
            "id": 9423,
            "name": "second_feature",
            "created_date": "2023-05-14T06:29:29.542708Z",
            "description": null,
            "initial_value": null,
            "default_enabled": false,
            "type": "STANDARD"
        },
        "feature_state_value": null,
        "environment": 5242,
        "identity": null,
        "feature_segment": null,
        "enabled": false
    }
]

```

To this:

```
[
    {
        "feature": {
            "id": 9422,
            "name": "first_feature",
            "type": "STANDARD"
        },
        "feature_state_value": null,
        "enabled": false
    },
    {
        "feature": {
            "id": 9423,
            "name": "second_feature",
            "type": "STANDARD"
        },
        "feature_state_value": null,
        "enabled": false
    }
]
```

The response for `/api/v1/identities` will change from this:

```
{
    "traits": [],
    "flags": [
        {
            "id": 27595,
            "feature": {
                "id": 9422,
                "name": "first_feature",
                "created_date": "2023-05-14T06:11:08.178802Z",
                "description": null,
                "initial_value": null,
                "default_enabled": false,
                "type": "STANDARD"
            },
            "feature_state_value": null,
            "environment": 5242,
            "identity": null,
            "feature_segment": null,
            "enabled": false
        },
        {
            "id": 27597,
            "feature": {
                "id": 9423,
                "name": "second_feature",
                "created_date": "2023-05-14T06:29:29.542708Z",
                "description": null,
                "initial_value": null,
                "default_enabled": false,
                "type": "STANDARD"
            },
            "feature_state_value": null,
            "environment": 5242,
            "identity": null,
            "feature_segment": null,
            "enabled": false
        }
    ]
}


```

To this

```
{
    "flags": [
        {
            "feature": {
                "id": 9422,
                "name": "first_feature",
                "type": "STANDARD"
            },
            "feature_state_value": null,
            "enabled": false
        },
        {
            "feature": {
                "id": 9423,
                "name": "second_one",
                "type": "STANDARD"
            },
            "feature_state_value": null,
            "enabled": false
        }
    ]
}
```
