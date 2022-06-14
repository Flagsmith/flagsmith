from django.urls import reverse
from rest_framework import status


def test_search_features(admin_client, feature, project):
    # First get the features without searching
    feature_list_url = reverse("api-v1:projects:project-features-list", args=[project])
    response = admin_client.get(feature_list_url)
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 1

    feature_name = response_json["results"][0]["name"]

    # Now search for the correct feature name
    valid_search_url = f"{feature_list_url}?search={feature_name}"
    valid_search_response = admin_client.get(valid_search_url)
    assert valid_search_response.status_code == status.HTTP_200_OK
    assert valid_search_response.json()["count"] == 1

    # Now search for an invalid feature name
    invalid_search_url = f"{feature_list_url}?search=invalid-feature"
    invalid_search_response = admin_client.get(invalid_search_url)
    assert invalid_search_response.status_code == status.HTTP_200_OK
    assert invalid_search_response.json()["count"] == 0


def test_sort_features(admin_client, project):
    # first, we need to create 2 features
    feature_1_data = {"name": "feature_a"}
    feature_2_data = {"name": "feature_b"}
    url = reverse("api-v1:projects:project-features-list", args=[project])

    feature_1_create_response = admin_client.post(url, data=feature_1_data)
    feature_2_create_response = admin_client.post(url, data=feature_2_data)

    assert feature_1_create_response.status_code == status.HTTP_201_CREATED
    assert feature_2_create_response.status_code == status.HTTP_201_CREATED

    feature_1_id = feature_1_create_response.json()["id"]
    feature_2_id = feature_2_create_response.json()["id"]

    # now we can test the ordering
    # by default it should sort by created_date asc
    created_date_asc_response = admin_client.get(url)
    assert created_date_asc_response.status_code == status.HTTP_200_OK
    created_date_asc_response_json = created_date_asc_response.json()
    assert created_date_asc_response_json["results"][0]["id"] == feature_1_id
    assert created_date_asc_response_json["results"][1]["id"] == feature_2_id

    # now let's try reversing the order
    created_date_desc_url = f"{url}?sort_direction=DESC"
    created_date_desc_response = admin_client.get(created_date_desc_url)
    assert created_date_desc_response.status_code == status.HTTP_200_OK
    created_date_desc_response_json = created_date_desc_response.json()
    assert created_date_desc_response_json["results"][0]["id"] == feature_2_id
    assert created_date_desc_response_json["results"][1]["id"] == feature_1_id

    # now let's try sorting by name asc and desc
    name_asc_url = f"{url}?sort_field=name&sort_direction=ASC"
    name_asc_response = admin_client.get(name_asc_url)
    assert name_asc_response.status_code == status.HTTP_200_OK
    name_asc_response_json = name_asc_response.json()
    assert name_asc_response_json["results"][0]["id"] == feature_1_id
    assert name_asc_response_json["results"][1]["id"] == feature_2_id

    name_desc_url = f"{url}?sort_field=name&sort_direction=DESC"
    name_desc_response = admin_client.get(name_desc_url)
    assert name_desc_response.status_code == status.HTTP_200_OK
    name_desc_response_json = name_desc_response.json()
    assert name_desc_response_json["results"][0]["id"] == feature_2_id
    assert name_desc_response_json["results"][1]["id"] == feature_1_id
