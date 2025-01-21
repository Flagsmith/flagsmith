import typing

from django.contrib import admin
from django.http import HttpRequest

from features.feature_health.models import FeatureHealthProvider
from features.feature_health.services import get_webhook_path_from_provider


@admin.register(FeatureHealthProvider)
class FeatureHealthProviderAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "type",
        "created_by",
        "webhook_url",
    )

    def changelist_view(
        self,
        request: HttpRequest,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.request = request
        return super().changelist_view(request, *args, **kwargs)

    def webhook_url(
        self,
        instance: FeatureHealthProvider,
    ) -> str:
        path = get_webhook_path_from_provider(instance)
        return self.request.build_absolute_uri(path)
