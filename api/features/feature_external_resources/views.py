import re

import structlog
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.response import Response

from features.models import Feature
from features.permissions import FeatureExternalResourcePermissions
from integrations.github.client import (
    get_github_issue_pr_title_and_state,
    label_github_issue_pr,
)
from integrations.github.models import GitHubRepository
from integrations.gitlab.models import GitLabConfiguration
from integrations.gitlab.services import register_webhook_for_resource
from organisations.models import Organisation

from .models import GITLAB_RESOURCE_TYPES, FeatureExternalResource, ResourceType
from .serializers import FeatureExternalResourceSerializer


@method_decorator(
    name="list",
    decorator=extend_schema(
        tags=["mcp"],
        extensions={
            "x-gram": {
                "name": "get_feature_external_resources",
                "description": "Retrieves external resources linked to the feature flag.",
            },
        },
    ),
)
class FeatureExternalResourceViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    serializer_class = FeatureExternalResourceSerializer
    permission_classes = [FeatureExternalResourcePermissions]

    def get_queryset(self):  # type: ignore[no-untyped-def]
        if getattr(self, "swagger_fake_view", False):
            return FeatureExternalResource.objects.none()

        if "pk" in self.kwargs:
            return FeatureExternalResource.objects.filter(id=self.kwargs["pk"])
        else:
            features_pk = self.kwargs["feature_pk"]
            return FeatureExternalResource.objects.filter(feature=features_pk)

    def list(self, request, *args, **kwargs) -> Response:  # type: ignore[no-untyped-def]
        queryset = self.get_queryset()  # type: ignore[no-untyped-call]
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        # get organisation id from feature and get feature from validated data
        organisation_id = get_object_or_404(
            Feature.objects.filter(id=self.kwargs["feature_pk"]),
        ).project.organisation_id

        # Add github issue/PR name to each linked external resource
        for resource in data if isinstance(data, list) else []:
            if ResourceType(resource["type"]) not in [
                ResourceType.GITHUB_ISSUE,
                ResourceType.GITHUB_PR,
            ]:
                continue

            if resource_url := resource.get("url"):
                resource["metadata"] = get_github_issue_pr_title_and_state(
                    organisation_id=organisation_id, resource_url=resource_url
                )

        return Response(data={"results": data})

    def create(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        resource_type = request.data.get("type")

        feature = get_object_or_404(
            Feature.objects.filter(
                id=self.kwargs["feature_pk"],
            ),
        )

        if resource_type in GITLAB_RESOURCE_TYPES:
            if config := GitLabConfiguration.objects.filter(
                project=feature.project,
            ).first():
                register_webhook_for_resource(
                    config=config,
                    resource_url=request.data.get("url"),
                )
            return super().create(request, *args, **kwargs)

        if resource_type not in (
            ResourceType.GITHUB_ISSUE,
            ResourceType.GITHUB_PR,
        ):
            return super().create(request, *args, **kwargs)

        github_configuration = (
            Organisation.objects.prefetch_related("github_config")
            .get(id=feature.project.organisation_id)
            .github_config.first()
        )

        if not github_configuration or not hasattr(feature.project, "github_project"):
            return Response(
                data={
                    "detail": "This Project doesn't have a valid GitHub integration configuration"
                },
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get repository owner and name, and issue/PR number from the external resource URL
        url = request.data.get("url")
        if request.data.get("type") == "GITHUB_PR":
            pattern = r"github.com/([^/]+)/([^/]+)/pull/(\d+)$"
        elif request.data.get("type") == "GITHUB_ISSUE":
            pattern = r"github.com/([^/]+)/([^/]+)/issues/(\d+)$"
        else:
            return Response(
                data={"detail": "Incorrect GitHub type"},
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST,
            )

        url_match = re.search(pattern, url)
        if url_match:
            owner, repo, issue = url_match.groups()
            if GitHubRepository.objects.get(
                github_configuration=github_configuration,
                repository_owner=owner,
                repository_name=repo,
            ).tagging_enabled:
                label_github_issue_pr(
                    installation_id=github_configuration.installation_id,
                    owner=owner,
                    repo=repo,
                    issue=issue,
                )
            response = super().create(request, *args, **kwargs)
            return response
        else:
            return Response(
                data={"detail": "Invalid GitHub Issue/PR URL"},
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST,
            )

    def perform_create(self, serializer: FeatureExternalResourceSerializer) -> None:  # type: ignore[override]
        resource = serializer.save()

        log_event_names: dict[ResourceType, tuple[str, str]] = {
            ResourceType.GITLAB_ISSUE: ("gitlab", "issue.linked"),
            ResourceType.GITLAB_MR: ("gitlab", "merge_request.linked"),
        }
        if (resource_type := ResourceType(resource.type)) in log_event_names:
            logger_name, event_name = log_event_names[resource_type]
            structlog.get_logger(logger_name).info(
                event_name,
                organisation__id=resource.feature.project.organisation_id,
                project__id=resource.feature.project_id,
                feature__id=resource.feature.id,
            )

    def perform_update(self, serializer):  # type: ignore[no-untyped-def]
        external_resource_id = int(self.kwargs["pk"])
        serializer.save(id=external_resource_id)
