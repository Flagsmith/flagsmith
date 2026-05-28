from rest_framework import serializers

_PR_STATE_CHOICES = ("active", "completed", "abandoned", "all")


class AdoBrowseQueryParamsSerializer(serializers.Serializer[None]):
    top = serializers.IntegerField(default=100, min_value=1, max_value=200)
    continuation_token = serializers.CharField(required=False, allow_blank=True)


class AdoRepositoriesQueryParamsSerializer(AdoBrowseQueryParamsSerializer):
    ado_project_id = serializers.CharField()


class AdoPullRequestsQueryParamsSerializer(AdoRepositoriesQueryParamsSerializer):
    state = serializers.ChoiceField(choices=_PR_STATE_CHOICES, default="active")


class AdoWorkItemsQueryParamsSerializer(AdoRepositoriesQueryParamsSerializer):
    # Override the base CharField — the work-items client interprets the
    # token as a non-negative integer offset into the WIQL ID list.
    # Validating here prevents negative-slice leaks and ValueErrors.
    # The ignore below is for the intentional field-type narrowing; DRF
    # supports replacing inherited field types but Mypy flags the variance.
    continuation_token = serializers.IntegerField(  # type: ignore[assignment]
        required=False, min_value=0
    )
    search_text = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True)
    work_item_type = serializers.CharField(required=False, allow_blank=True)
