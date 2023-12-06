from datetime import timedelta
from unittest import mock

import freezegun
import pytest
from django.utils import timezone

from environments.models import Environment
from features.constants import STALE_FLAGS_TAG_LABEL
from features.models import Feature, FeatureState
from features.tasks import (
    tag_stale_flags,
    trigger_feature_state_change_webhooks,
)
from organisations.models import Organisation
from projects.models import Project
from projects.tags.models import Tag
from webhooks.webhooks import WebhookEventType


@pytest.mark.django_db
@mock.patch("features.tasks.Thread")
def test_trigger_feature_state_change_webhooks(MockThread):
    # Given
    initial_value = "initial"
    new_value = "new"

    organisation = Organisation.objects.create(name="Test organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    environment = Environment.objects.create(name="Test environment", project=project)
    feature = Feature.objects.create(
        name="Test feature", project=project, initial_value=initial_value
    )
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)

    # update the feature state value and save both objects to ensure that the history is updated
    feature_state.feature_state_value.string_value = new_value
    feature_state.feature_state_value.save()
    feature_state.save()

    MockThread.reset_mock()  # reset mock as it will have been called when setting up the data

    # When
    trigger_feature_state_change_webhooks(feature_state)

    # Then
    call_list = MockThread.call_args_list

    environment_webhook_call_args = call_list[0]
    organisation_webhook_call_args = call_list[1]

    # verify that the data for both calls is the same
    assert (
        environment_webhook_call_args[1]["args"][1]
        == organisation_webhook_call_args[1]["args"][1]
    )

    data = environment_webhook_call_args[1]["args"][1]
    event_type = environment_webhook_call_args[1]["args"][2]
    assert data["new_state"]["feature_state_value"] == new_value
    assert data["previous_state"]["feature_state_value"] == initial_value
    assert event_type == WebhookEventType.FLAG_UPDATED


@pytest.mark.django_db
@mock.patch("features.tasks.Thread")
def test_trigger_feature_state_change_webhooks_for_deleted_flag(
    MockThread, organisation, project, environment, feature
):
    # Given
    new_value = "new"
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)

    # update the feature state value and save both objects to ensure that the history is updated
    feature_state.feature_state_value.string_value = new_value
    feature_state.feature_state_value.save()
    feature_state.save()

    MockThread.reset_mock()  # reset mock as it will have been called when setting up the data
    trigger_feature_state_change_webhooks(feature_state, WebhookEventType.FLAG_DELETED)

    # Then
    call_list = MockThread.call_args_list

    environment_webhook_call_args = call_list[0]
    organisation_webhook_call_args = call_list[1]

    # verify that the data for both calls is the same
    assert (
        environment_webhook_call_args[1]["args"][1]
        == organisation_webhook_call_args[1]["args"][1]
    )

    data = environment_webhook_call_args[1]["args"][1]
    event_type = environment_webhook_call_args[1]["args"][2]
    assert data["new_state"] is None
    assert data["previous_state"]["feature_state_value"] == new_value
    assert event_type == WebhookEventType.FLAG_DELETED


def test_tag_stale_flags(organisation: Organisation):
    # Given
    now = timezone.now()

    # a project with a stale flag, a not-stale flag, and a permanent flag
    project_1 = Project.objects.create(name="project_1", organisation=organisation)
    Environment.objects.create(
        name="p1_env", project=project_1, use_v2_feature_versioning=True
    )
    p1_not_stale_flag = Feature.objects.create(
        name="p1_not_stale_flag", project=project_1
    )
    permanent_tag = Tag.objects.create(
        label="permanent", project=project_1, is_permanent=True
    )
    p1_permanent_flag = Feature.objects.create(
        name="p1_permanent_flag", project=project_1
    )
    p1_permanent_flag.tags.add(permanent_tag)

    with freezegun.freeze_time(
        now - timedelta(days=project_1.stale_flags_limit_days + 1)
    ):
        p1_stale_flag = Feature.objects.create(name="p1_stale_flag", project=project_1)

    # and a project with no stale flags
    project_2 = Project.objects.create(name="project_2", organisation=organisation)
    Environment.objects.create(
        name="p2_env", project=project_2, use_v2_feature_versioning=True
    )
    p2_not_stale_flag = Feature.objects.create(
        name="p2_not_stale_flag", project=project_2
    )

    # and a project which has no environments using v2 feature versioning
    project_3 = Project.objects.create(name="project_3", organisation=organisation)
    Environment.objects.create(
        name="p3_env", project=project_3, use_v2_feature_versioning=False
    )
    p3_not_stale_flag = Feature.objects.create(
        name="p3_not_stale_flag", project=project_3
    )

    # When
    tag_stale_flags()

    # Then
    # the stale flag in project 1 is tagged correctly
    p1_stale_flags_tag = Tag.objects.filter(
        project=project_1, label=STALE_FLAGS_TAG_LABEL
    ).first()
    assert p1_stale_flags_tag is not None
    assert p1_stale_flags_tag in p1_stale_flag.tags.all()
    # but the active flag and permanent flags are not tagged
    assert p1_stale_flags_tag not in p1_not_stale_flag.tags.all()
    assert p1_stale_flags_tag not in p1_permanent_flag.tags.all()

    # and the tag is not created in project_2, and no tags are assigned to the active flag
    assert not Tag.objects.filter(
        project=project_2, label=STALE_FLAGS_TAG_LABEL
    ).exists()
    assert p2_not_stale_flag.tags.count() == 0

    # and the tag is not created in project_3, and no tags are assigned to the active flag
    assert not Tag.objects.filter(
        project=project_3, label=STALE_FLAGS_TAG_LABEL
    ).exists()
    assert p3_not_stale_flag.tags.count() == 0
