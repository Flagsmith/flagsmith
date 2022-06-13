from django.urls import reverse


def test_search_features(admin_client, feature, project):
    # First get the features without searching
    feature_list_url = reverse("api-v1:projects:project-features-list", args=[project])
    response = admin_client.get(feature_list_url)
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["count"] == 1

    feature_name = response_json["results"][0]["name"]

    # Now search for the correct feature name
    valid_search_url = f"{feature_list_url}?search={feature_name}"
    valid_search_response = admin_client.get(valid_search_url)
    assert valid_search_response.status_code == 200
    assert valid_search_response.json()["count"] == 1

    # Now search for an invalid feature name
    invalid_search_url = f"{feature_list_url}?search=invalid-feature"
    invalid_search_response = admin_client.get(invalid_search_url)
    assert invalid_search_response.status_code == 200
    assert invalid_search_response.json()["count"] == 0
