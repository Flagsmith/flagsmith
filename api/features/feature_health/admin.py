import typing

from django.contrib import admin
from django.http import HttpRequest

from features.feature_health.models import FeatureHealthProvider
from features.feature_health.providers.services import (
    get_webhook_path_from_provider,
)


@admin.register(FeatureHealthProvider)
class FeatureHealthProviderAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "project",
        "name",
        "created_by",
        "webhook_url",
    )

    def changelist_view(  # type: ignore[override]
        self,
        request: HttpRequest,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.request = request
        return super().changelist_view(request, *args, **kwargs)  # type: ignore[return-value]

    def webhook_url(
        self,
        instance: FeatureHealthProvider,
    ) -> str:
        path = get_webhook_path_from_provider(instance)
        return self.request.build_absolute_uri(path)
