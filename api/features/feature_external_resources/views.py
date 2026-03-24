import re
from typing import Any

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
from integrations.gitlab.client import (
    label_gitlab_issue_mr,
)
from organisations.models import Organisation

from .models import FeatureExternalResource
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

    # Override get list view to add github issue/pr name to each linked external resource
    def list(self, request, *args, **kwargs) -> Response:  # type: ignore[no-untyped-def]
        queryset = self.get_queryset()  # type: ignore[no-untyped-call]
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        # get organisation id from feature and get feature from validated data
        organisation_id = get_object_or_404(
            Feature.objects.filter(id=self.kwargs["feature_pk"]),
        ).project.organisation_id

        for resource in data if isinstance(data, list) else []:
            if resource_url := resource.get("url"):
                resource_type = resource.get("type", "")
                if resource_type.startswith("GITHUB_"):
                    resource["metadata"] = get_github_issue_pr_title_and_state(
                        organisation_id=organisation_id, resource_url=resource_url
                    )
                elif resource_type.startswith("GITLAB_"):
                    try:
                        import re as _re

                        from integrations.gitlab.client import (
                            get_gitlab_issue_mr_title_and_state as get_gitlab_metadata,
                        )
                        from integrations.gitlab.models import (
                            GitLabConfiguration,
                        )

                        feature_obj = get_object_or_404(
                            Feature.objects.filter(id=self.kwargs["feature_pk"]),
                        )
                        gitlab_config = GitLabConfiguration.objects.filter(
                            project=feature_obj.project, deleted_at__isnull=True
                        ).first()
                        if gitlab_config and gitlab_config.gitlab_project_id:
                            # Parse resource IID from URL
                            if resource_type == "GITLAB_MR":
                                match = _re.search(
                                    r"https?://[^/]+/([^/]+(?:/[^/]+)*)/-/merge_requests/(\d+)$",
                                    resource_url,
                                )
                                api_type = "merge_requests"
                            else:
                                match = _re.search(
                                    r"https?://[^/]+/([^/]+(?:/[^/]+)*)/-/(?:issues|work_items)/(\d+)$",
                                    resource_url,
                                )
                                api_type = "issues"

                            if match:
                                _project_path, iid = match.group(1), int(match.group(2))
                                resource["metadata"] = get_gitlab_metadata(
                                    instance_url=gitlab_config.gitlab_instance_url,
                                    access_token=gitlab_config.access_token,
                                    gitlab_project_id=gitlab_config.gitlab_project_id,
                                    resource_type=api_type,
                                    resource_iid=iid,
                                )
                    except Exception:
                        pass

        return Response(data={"results": data})

    def _create_gitlab_resource(
        self, request: Any, feature: Any, resource_type: str, *args: Any, **kwargs: Any
    ) -> Response:
        from integrations.gitlab.models import GitLabConfiguration

        try:
            gitlab_config = GitLabConfiguration.objects.get(
                project=feature.project,
                deleted_at__isnull=True,
            )
        except GitLabConfiguration.DoesNotExist:
            return Response(
                data={
                    "detail": "This Project doesn't have a valid GitLab integration configuration"
                },
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST,
            )

        url = request.data.get("url")
        if resource_type == "GITLAB_MR":
            pattern = r"https?://[^/]+/([^/]+(?:/[^/]+)*)/-/merge_requests/(\d+)$"
        else:
            pattern = (
                r"https?://[^/]+/([^/]+(?:/[^/]+)*)/-/(?:issues|work_items)/(\d+)$"
            )

        url_match = re.search(pattern, url)
        if url_match:
            _project_path, resource_iid = url_match.groups()
            api_resource_type = (
                "merge_requests" if resource_type == "GITLAB_MR" else "issues"
            )
            if gitlab_config.tagging_enabled and gitlab_config.gitlab_project_id:
                label_gitlab_issue_mr(
                    instance_url=gitlab_config.gitlab_instance_url,
                    access_token=gitlab_config.access_token,
                    gitlab_project_id=gitlab_config.gitlab_project_id,
                    resource_type=api_resource_type,
                    resource_iid=int(resource_iid),
                )
            return super().create(request, *args, **kwargs)
        else:
            return Response(
                data={"detail": "Invalid GitLab Issue/MR URL"},
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _create_github_resource(
        self, request: Any, feature: Any, resource_type: str, *args: Any, **kwargs: Any
    ) -> Response:
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
        if resource_type == "GITHUB_PR":
            pattern = r"github.com/([^/]+)/([^/]+)/pull/(\d+)$"
        elif resource_type == "GITHUB_ISSUE":
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

    def create(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        feature = get_object_or_404(
            Feature.objects.filter(
                id=self.kwargs["feature_pk"],
            ),
        )

        resource_type = request.data.get("type", "")

        # Handle GitLab resources
        if resource_type in ("GITLAB_MR", "GITLAB_ISSUE"):
            return self._create_gitlab_resource(
                request, feature, resource_type, *args, **kwargs
            )

        # Handle GitHub resources
        return self._create_github_resource(
            request, feature, resource_type, *args, **kwargs
        )

    def perform_update(self, serializer):  # type: ignore[no-untyped-def]
        external_resource_id = int(self.kwargs["pk"])
        serializer.save(id=external_resource_id)
