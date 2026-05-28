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
    search_text = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True)
    work_item_type = serializers.CharField(required=False, allow_blank=True)
