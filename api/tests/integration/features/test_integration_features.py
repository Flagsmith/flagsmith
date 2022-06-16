import json

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


def test_filter_features_by_tags(admin_client, project):
    # first lets create some tags
    tag_labels = ("tag_1", "tag_2")

    tags_url = reverse("api-v1:projects:tags-list", args=[project])

    tag_ids = []
    for tag_label in tag_labels:
        response = admin_client.post(
            tags_url, data={"label": tag_label, "color": "#ffffff"}
        )
        assert response.status_code == status.HTTP_201_CREATED, f"{tag_label} failed."
        tag_ids.append(response.json()["id"])

    # now, let's create a feature with one of the tags and one without any
    features_url = reverse("api-v1:projects:project-features-list", args=[project])
    tagged_feature_response = admin_client.post(
        features_url,
        data=json.dumps(
            {"name": "tagged_feature", "project": project, "tags": [tag_ids[0]]}
        ),
        content_type="application/json",
    )
    assert tagged_feature_response.status_code == status.HTTP_201_CREATED
    tagged_feature_id = tagged_feature_response.json()["id"]

    untagged_feature_response = admin_client.post(
        features_url,
        data=json.dumps({"name": "untagged_feature", "project": project, "tags": []}),
        content_type="application/json",
    )
    assert untagged_feature_response.status_code == status.HTTP_201_CREATED
    untagged_feature_id = untagged_feature_response.json()["id"]

    # now lets try listing features with different combinations of tag filters to
    # check we get what we expect
    # case 1: no tags filter should return all features
    assert admin_client.get(features_url).json()["count"] == 2

    # case 2: empty tags filter should return untagged feature only
    tagged_feature_url = f"{features_url}?tags="
    tagged_feature_response = admin_client.get(tagged_feature_url)
    tagged_feature_response_json = tagged_feature_response.json()
    assert tagged_feature_response_json["count"] == 1
    assert tagged_feature_response_json["results"][0]["id"] == untagged_feature_id

    # case 3: filter for tagged feature's tag should return tagged feature only
    tagged_feature_url = f"{features_url}?tags={tag_ids[0]}"
    tagged_feature_response = admin_client.get(tagged_feature_url)
    tagged_feature_response_json = tagged_feature_response.json()
    assert tagged_feature_response_json["count"] == 1
    assert tagged_feature_response_json["results"][0]["id"] == tagged_feature_id

    # case 4: filter for all tags should return no features
    all_tags_features_url = f"{features_url}?tags={tag_ids[0]},{tag_ids[1]}"
    all_tags_features_response = admin_client.get(all_tags_features_url)
    all_tags_features_response_json = all_tags_features_response.json()
    assert all_tags_features_response_json["count"] == 0


def test_filter_features_by_archived_status(admin_client, project):
    # First let's create 2 new features, one which is archived and one which isn't
    features_url = reverse("api-v1:projects:project-features-list", args=[project])
    create_archived_feature_response = admin_client.post(
        features_url,
        data={
            "name": "archived_feature",
            "project": project,
            # in practice, it makes no sense to create a feature with is_archived=true,
            # but it simplifies the test setup here.
            "is_archived": True,
        },
    )
    assert create_archived_feature_response.status_code == status.HTTP_201_CREATED
    archived_feature_id = create_archived_feature_response.json()["id"]

    create_unarchived_feature_response = admin_client.post(
        features_url, data={"name": "unarchived_feature", "project": project}
    )
    assert create_unarchived_feature_response.status_code == status.HTTP_201_CREATED
    unarchived_feature_id = create_unarchived_feature_response.json()["id"]

    # Now let's verify that the correct features are returned based on the is_archived
    # query parameter
    # Case 1: is_archived not provided - both features should be returned
    list_features_missing_is_archived_response = admin_client.get(features_url)
    assert list_features_missing_is_archived_response.status_code == status.HTTP_200_OK
    assert list_features_missing_is_archived_response.json()["count"] == 2

    # Case 2: is_archived=false should return only unarchived feature
    list_features_is_archived_false_url = f"{features_url}?is_archived=false"
    list_features_is_archived_false_response = admin_client.get(
        list_features_is_archived_false_url
    )
    assert list_features_is_archived_false_response.status_code == status.HTTP_200_OK
    assert list_features_is_archived_false_response.json()["count"] == 1
    assert (
        list_features_is_archived_false_response.json()["results"][0]["id"]
        == unarchived_feature_id
    )

    # Case 3: is_archived=true should return archived feature
    list_features_is_archived_true_url = f"{features_url}?is_archived=true"
    list_features_is_archived_true_response = admin_client.get(
        list_features_is_archived_true_url
    )
    assert list_features_is_archived_true_response.status_code == status.HTTP_200_OK
    assert list_features_is_archived_true_response.json()["count"] == 1
    assert (
        list_features_is_archived_true_response.json()["results"][0]["id"]
        == archived_feature_id
    )
