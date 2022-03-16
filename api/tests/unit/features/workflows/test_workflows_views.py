import json

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from features.models import FeatureState
from features.workflows.models import ChangeRequest, ChangeRequestApproval
from users.models import FFAdminUser


def test_create_change_request(
    feature, environment, admin_client, organisation_one_user
):
    # Given
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)
    data = {
        "title": "My change request",
        "description": "Some useful description",
        "from_feature_state": feature_state.id,
        "to_feature_state": {
            "enabled": True,
            "feature_state_value": {"type": "unicode", "string_value": "foobar"},
            "multivariate_feature_state_values": [],
        },
        "approvals": [{"user": organisation_one_user.id, "required": True}],
    }
    url = reverse("api-v1:features:workflows:change-requests-list")

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    # The request is successful
    assert response.status_code == status.HTTP_201_CREATED

    # and the change request is stored and the correct values are updated
    response_json = response.json()
    assert response_json["id"]
    assert response_json["created_at"]
    assert response_json["updated_at"]

    # and it has the correct approvals
    change_request = ChangeRequest.objects.get(id=response_json["id"])
    assert change_request.approvals.count() == 1
    assert change_request.approvals.first().user == organisation_one_user

    # and the to_feature_state object is created with the expected information
    to_feature_state_id = response_json["to_feature_state"]["id"]
    to_feature_state = FeatureState.objects.get(id=to_feature_state_id)
    assert to_feature_state.environment == feature_state.environment
    assert to_feature_state.feature == feature_state.feature
    assert to_feature_state.feature_segment == feature_state.feature_segment
    assert to_feature_state.identity == feature_state.identity
    assert to_feature_state.version is None
    assert to_feature_state.live_from is None
    assert (
        to_feature_state.get_feature_state_value()
        == data["to_feature_state"]["feature_state_value"]["string_value"]
    )


def test_approve_change_request_when_no_required_approvals(
    change_request_no_required_approvals, organisation_one_user
):
    # Given
    organisation_one_user_client = APIClient()
    organisation_one_user_client.force_authenticate(organisation_one_user)

    url = reverse(
        "api-v1:features:workflows:change-requests-approve",
        args=(change_request_no_required_approvals.id,),
    )

    # When
    response = organisation_one_user_client.post(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    # a new approval object exists for the change request now
    assert change_request_no_required_approvals.approvals.count() == 1
    approval = change_request_no_required_approvals.approvals.first()
    assert approval.user == organisation_one_user
    assert approval.approved_at


def test_approve_change_request_when_required_approvals_for_same_user(
    change_request_no_required_approvals, organisation_one_user
):
    # Given
    organisation_one_user_client = APIClient()
    organisation_one_user_client.force_authenticate(organisation_one_user)

    approval = ChangeRequestApproval.objects.create(
        user=organisation_one_user, change_request=change_request_no_required_approvals
    )

    url = reverse(
        "api-v1:features:workflows:change-requests-approve",
        args=(change_request_no_required_approvals.id,),
    )

    # When
    response = organisation_one_user_client.post(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    # the existing approval record is updated correctly
    assert change_request_no_required_approvals.approvals.count() == 1
    approval.refresh_from_db()
    assert approval.approved_at


def test_approve_change_request_when_required_approvals_for_another_user(
    change_request_no_required_approvals, organisation_one_user, organisation_one
):
    # Given
    organisation_one_user_client = APIClient()
    organisation_one_user_client.force_authenticate(organisation_one_user)

    another_user = FFAdminUser.objects.create(email="another_user@organisationone.com")
    another_user.add_organisation(organisation_one)

    existing_approval = ChangeRequestApproval.objects.create(
        user=organisation_one_user, change_request=change_request_no_required_approvals
    )

    url = reverse(
        "api-v1:features:workflows:change-requests-approve",
        args=(change_request_no_required_approvals.id,),
    )

    # When
    response = organisation_one_user_client.post(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    # the existing approval record is not affected and a new one is created
    assert change_request_no_required_approvals.approvals.count() == 2

    existing_approval.refresh_from_db()
    assert existing_approval.approved_at is None

    created_approval = change_request_no_required_approvals.approvals.last()
    assert created_approval.user == organisation_one_user
    assert created_approval.approved_at


def test_commit_change_request_missing_required_approvals(
    change_request_no_required_approvals, admin_client, organisation_one_user
):
    # Given
    ChangeRequestApproval.objects.create(
        user=organisation_one_user, change_request=change_request_no_required_approvals
    )

    url = reverse(
        "api-v1:features:workflows:change-requests-commit",
        args=(change_request_no_required_approvals.id,),
    )

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    change_request_no_required_approvals.refresh_from_db()
    assert change_request_no_required_approvals.committed_at is None
    assert change_request_no_required_approvals.to_feature_state.version is None


def test_commit_approved_change_request(
    change_request_no_required_approvals, admin_client, organisation_one_user, mocker
):
    # Given
    now = timezone.now()
    ChangeRequestApproval.objects.create(
        user=organisation_one_user,
        change_request=change_request_no_required_approvals,
        required=True,
        approved_at=now,
    )

    mocker.patch("features.workflows.models.timezone.now", return_value=now)

    url = reverse(
        "api-v1:features:workflows:change-requests-commit",
        args=(change_request_no_required_approvals.id,),
    )

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    change_request_no_required_approvals.refresh_from_db()
    assert change_request_no_required_approvals.committed_at == now
    assert change_request_no_required_approvals.to_feature_state.version == 2
    assert change_request_no_required_approvals.to_feature_state.live_from == now
