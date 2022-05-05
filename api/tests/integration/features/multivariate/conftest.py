import json

import pytest
from django.urls import reverse


@pytest.fixture()
def mv_option_50_percent(project, admin_client, feature):
    url = reverse(
        "api-v1:projects:feature-mv-options-list",
        args=[project, feature],
    )
    data = {
        "type": "unicode",
        "feature": feature,
        "string_value": "bigger",
        "default_percentage_allocation": 50,
    }
    return admin_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    ).json()["id"]
