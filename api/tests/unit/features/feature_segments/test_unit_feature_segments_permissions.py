from unittest.mock import MagicMock, patch

from rest_framework.permissions import IsAuthenticated

from features.feature_segments.permissions import FeatureSegmentPermissions


def test_has_permission_when_super_returns_false():  # type: ignore[no-untyped-def]  # noqa: E501
    permission = FeatureSegmentPermissions()
    request = MagicMock()
    view = MagicMock()
    with patch.object(IsAuthenticated, "has_permission", return_value=False):
        result = permission.has_permission(request, view)  # type: ignore[no-untyped-call]
        assert result is False


def test_feature_permission_return_true_if_view_action_is_list():  # type: ignore[no-untyped-def]  # noqa: E501
    # GIVEN
    permission = FeatureSegmentPermissions()

    request = MagicMock()
    view = MagicMock()
    view.action = "list"
    view.detail = None

    # WHEN
    result = permission.has_permission(request, view)  # type: ignore[no-untyped-call]

    # THEN
    assert result is True


def test_feature_permission_return_true_if_view_action_is_get_by_uuid():  # type: ignore[no-untyped-def]  # noqa: E501
    # GIVEN
    permission = FeatureSegmentPermissions()

    request = MagicMock()
    view = MagicMock()
    view.action = "get_by_uuid"
    view.detail = None

    # WHEN
    result = permission.has_permission(request, view)  # type: ignore[no-untyped-call]

    # THEN
    assert result is True


def test_feature_permission_return_true_if_view_action_is_update_priorities():  # type: ignore[no-untyped-def]  # noqa: E501
    # GIVEN
    permission = FeatureSegmentPermissions()

    request = MagicMock()
    view = MagicMock()
    view.action = "update_priorities"
    view.detail = None

    # WHEN
    result = permission.has_permission(request, view)  # type: ignore[no-untyped-call]

    # THEN
    assert result is True


def test_feature_permission_return_true_if_view_details_is_not_falsy():  # type: ignore[no-untyped-def]  # noqa: E501
    # GIVEN
    permission = FeatureSegmentPermissions()

    request = MagicMock()
    view = MagicMock()
    view.action = "anything"
    view.detail = "anything"

    # WHEN
    result = permission.has_permission(request, view)  # type: ignore[no-untyped-call]

    # THEN
    assert result is True


def test_feature_permission_return_false_if_view_action_is_unsupported():  # type: ignore[no-untyped-def]  # noqa: E501
    # GIVEN
    permission = FeatureSegmentPermissions()

    request = MagicMock()
    view = MagicMock()
    view.action = "anything"
    view.detail = None

    # WHEN
    result = permission.has_permission(request, view)  # type: ignore[no-untyped-call]

    # THEN
    assert result is False


def test_feature_permission_pass_empty_list_of_tags_if_feature_id_is_not_provided():  # type: ignore[no-untyped-def]  # noqa: E501
    # GIVEN
    permission = FeatureSegmentPermissions()
    fake_env = MagicMock()

    request = MagicMock()
    request.data = {"environment": "1", "feature": None}
    request.user.has_environment_permission.return_value = True

    view = MagicMock()
    view.action = "create"
    view.detail = None

    # WHEN
    with patch("environments.models.Environment.objects.get", return_value=fake_env):
        result = permission.has_permission(request, view)  # type: ignore[no-untyped-call]

        # THEN
        assert result is True
        request.user.has_environment_permission.assert_called_once_with(
            permission="MANAGE_SEGMENT_OVERRIDES",
            environment=fake_env,
            tag_ids=[],
        )


def test_feature_permission_pass_list_of_tags_if_feature_id_is_provided():  # type: ignore[no-untyped-def]  # noqa: E501
    # GIVEN
    permission = FeatureSegmentPermissions()
    fake_env = MagicMock()
    fake_feature = MagicMock()
    fake_feature.tags.values_list.return_value = [1, 2, 3]

    request = MagicMock()
    request.data = {"environment": "1", "feature": "1"}
    request.user.has_environment_permission.return_value = True

    view = MagicMock()
    view.action = "create"
    view.detail = None

    # WHEN
    with patch("environments.models.Environment.objects.get", return_value=fake_env):
        with patch("features.models.Feature.objects.get", return_value=fake_feature):
            result = permission.has_permission(request, view)  # type: ignore[no-untyped-call]

            # THEN
            assert result is True
            request.user.has_environment_permission.assert_called_once_with(
                permission="MANAGE_SEGMENT_OVERRIDES",
                environment=fake_env,
                tag_ids=[1, 2, 3],
            )
